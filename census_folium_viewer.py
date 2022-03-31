# Census Folium Viewer:
# A set of functions for creating interactive choropleth maps
# of US Census Data using Folium
# By Kenneth Burchfiel 
# Released under the MIT license

# Citation info for color_schemes_from_branca.json:
# Source: https://github.com/python-visualization/branca/blob/master/branca/_schemes.json
# I believe these schemes were originally created by Cynthia Brewer, and are
# licensed under the Apache License, Version 2.0. See:
#  http://www.personal.psu.edu/cab38/ColorBrewer/ColorBrewer_updates.html

# A sizeable portion of the choropleth mapping code
# came from Amodiovalerio Verde's excellent interactive
# choropleth tutorial at
# https://vverde.github.io/blob/interactivechoropleth.html .
# Amodiovalerio informed me via email that there are "no specific
# licences for the code of interactivechoropleth. 
# You're free to use the code. A mention/link will be appreciated."
# Thank you, Amodiovalerio!

import geopandas
import folium
from folium.plugins import FloatImage
import pandas as pd
import time
from selenium import webdriver
import numpy as np
import json
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
import branca.colormap as cm

def create_vertical_legend(bins, data_variable_text, map_name, path_to_legends, 
color_list, variable_decimals):
    '''This function allows you to insert a vertically oriented legend, built
    using matplotlib, into your map. I find that vertical legends provide more
    room for data labels than does the default horizontal legend. In addition,
    this legend should remain mostly readable against both dark
    and light backgrounds.'''

    y_axes_max = 4 # The highest length of the y axes
    bar_count = len(color_list) # The number of color bars that will be plotted
    bar_height = y_axes_max/bar_count # There is no space in between the color
    # bars, as in the default legend.
    y_axes = np.arange(0, y_axes_max, bar_height) # Sets reference points
    # for plotting the bars

    fig, axes = plt.subplots(nrows = 2, ncols = 3, figsize = [2, 8], 
    gridspec_kw = {'width_ratios': [1, 2, 1]})
    # This plot will actually have 6 subplots, although the color bars will
    # exist within just one plot (the bottom middle one). The extra subplots
    # were added to provide extra space for the title, which would otherwise
    # be confined to a relatively narrow plot.
    # gridspec_kw is used to reduce the width of the left and right subplots.
    # See https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.subplots.html
    # and https://matplotlib.org/stable/api/_as_gen/matplotlib.gridspec.GridSpec.html .


    # Next, the function creates a horizontal bar chart with equally spaced 
    # bars. The bars are given the colors provided within color_list.
    axes[1][1].barh(y = y_axes, width = 0.1, height = bar_height, 
    color = color_list) # These bars will be opaque so that their colors
    # are not skewed by their position on the map.
    plt.subplots_adjust(hspace = 0) # Removes extra spaces in between subplots
    # axes.set_yticks(y_axes, labels = bins)
    # Next, the function adds labels representing different regions of the 
    # data to the bar chart. The idea is to locate each color in between
    # two data points, as seen in the default legend. The positioning of the
    # numbers varies somewhat depending on how many bars are being plotted,
    # but the spacing specified below works pretty well across a range of
    # bar counts.
    # path_effects is used to add an outline to the text to make it more 
    # readable against varying background colors. See 
    # https://matplotlib.org/stable/tutorials/advanced/patheffects_guide.html
    for i in range(len(bins)):
        axes[1][1].text(0.05, bar_height*i + bar_height*-0.35, 
        round(bins[i],variable_decimals), ha = 'center', va = 'top', 
        fontweight = 'bold', color = 'black', size = 12,
        path_effects = (
            [path_effects.Stroke(linewidth=1, foreground='white'),
            path_effects.Normal()]))
    # The function next adds a title to the legend (on top of the bar chart).
    axes[0][1].text(0.5, 0, data_variable_text, va = 'bottom', wrap = True,
    color = 'white', size = 12, ha = 'center', path_effects = (
        [path_effects.Stroke(linewidth=2, foreground='black'), 
        path_effects.Normal()]))
    # Since the axes don't need to display within the legend, they 
    # can be removed, which the following for loop accomplishes.
    for i in range(2):
        for j in range(3):
            axes[i][j].spines['bottom'].set_visible(False)
            # [i][j] is used because there are two sets of subplots within 
            # the graph.
            # Based on G M's response at:
            # https://stackoverflow.com/a/54768749/13097194
            axes[i][j].spines['left'].set_visible(False)
            axes[i][j].spines['right'].set_visible(False)
            axes[i][j].spines['top'].set_visible(False)
            axes[i][j].get_xaxis().set_visible(False) # Based on 
            # Also based on G M's response at:
            # https://stackoverflow.com/questions/2176424/hiding-axis-text-in-matplotlib-plots
            axes[i][j].get_yaxis().set_visible(False) 
    
    # Finally, the plot is saved to an .svg file that can be read into 
    # the Folium map as a FloatImage object.
    # function can read
    plt.savefig(path_to_legends+map_name+'_legend.svg', transparent = True)
    # See https://stackoverflow.com/a/4708018/13097194
    # print("Saving to:",path_to_legends+map_name+'_legend.svg')
    # plt.show()


def prepare_zip_table(shapefile_path, shape_feature_name, 
data_path, data_feature_name, tolerance = 0.005):
    '''This function merges US Census zip code shapefile data with
    Census zip-code-level demographic data in order to create a DataFrame 
    that can be used to generate choropleth maps.
    Variables:
    shapefile_path: The path to the .shp file that contains the shapefile 
    data (e.g. zip code boundaries) to include within the table.
    shape_feature_name: The name of the column within the shapefile table that
    contains the name of the shapes. For example, for the 2020 zip code
    shapefile data that I downloaded, the column name in the US Census
    shapefile happened to be ZCTA5CE20, and contained zip code names (22101,
    05753, etc).
    data_path: The path to a .csv file containing US Census data.
    data_feature_name: The name of the column within the US Census data .csv
    file that contains shape names (e.g. zip code boundaries). This column,
    along with the column referred to by shape_feature_name, will be used
    to merge the shapefile and US Census data tables together. 
    tolerance: The extent to which the shapefiles will be simplified.
    Lower tolerance values result in more accurate shape boundaries but also
    longer processing times and larger file sizes. I have found 0.005 to work
    pretty well for zip code maps.
    Note: on one day when using prepare_zip_table, I received the following 
    error message:
    "ImportError: the 'read_file' function requires the 'fiona' package, 
    but it is not installed or does not import correctly.
    Importing fiona resulted in: DLL load failed while importing ogrext:
    The specified module could not be found."
    I received this error while using version 3.4.0 of GDAL and version 1.8.20 
    of fiona. After trying a couple different uninstall/reinstall operations, 
    I was able to resolve the error by force removing both GDAL and Fiona, 
    then installing
    fiona 1.8.19 (as suggested by Abhiram at
    https://stackoverflow.com/a/69534619/13097194). Conda Forge installed 
    GDAL 3.2.2 as part of this operation, and these two
    seem to work together well.
    '''

    print("Reading shape data:")
    shape_data = geopandas.read_file(shapefile_path)
    shape_data[shape_feature_name] = shape_data[
        shape_feature_name].astype(str).str.pad(5, fillchar = '0')
    # The above line converts the zip code values into strings (if they were 
    # not already in that format), then adds extra 0s via str.pad to any
    # zip codes with fewer than 5 digits. This prevents data merging errors
    # related to zip codes with leading zeroes. For instance, if a shapefile
    # represented the zip 05753 as 5753, but a data file represented it as
    # 05753, the two zip codes would not merge. Adding in str.pad prevents
    # this issue.

    # To reduce the time needed to produce the choropleth map and to 
    # decrease its file size, the function next uses  Geopandas' simplify()
    # function to reduce the complexity of the shape coordinates stored in the
    # geometry column. See
    # https://geopandas.org/en/stable/docs/reference/api/geopandas.GeoSeries.simplify.html
    # and (for more detail)
    # https://shapely.readthedocs.io/en/latest/manual.html#object.simplify .
    print("Simplifying shape data:") # This can take a little while
    shape_data['geometry'] = shape_data.simplify(tolerance = tolerance)
    # The function next imports census data.
    print("Reading census data:")
    census_data = pd.read_csv(data_path)
    census_data[data_feature_name] = census_data[data_feature_name].astype(
        str).str.pad(5, fillchar = '0')
    # Once again, str.pad is used to ensure that all zip codes contain
    # five digits.
    # Next, to make it easier to create choropleth maps, the function merges
    # the shapefile and census data tables.
    print("Merging shape and data tables:")
    merged_shape_data_table = pd.merge(shape_data, census_data, 
    left_on = shape_feature_name, right_on = data_feature_name)
    return merged_shape_data_table

def prepare_county_table(shapefile_path, shape_state_code_column, 
shape_county_code_column, tolerance, data_path, data_state_code_column, 
data_county_code_column):
    '''This function merges US Census county shapefile data with
    Census county-level demographic data in order to create a DataFrame 
    that can be used to generate choropleth maps.
    shape_state_code_column and shape_county_code_column refer to numerical
    state and county codes stored within the .shp shapefile document. 
    data_state_code_column and data_county_code_column refer to equivalent
    codes stored within the .csv Census data document. These codes will 
    be used to merge the shapefile and Census data tables together.
    
    See the documentation for prepare_zip_table for more information on
    this function.'''

    print("Reading shape data:")
    shape_data = geopandas.read_file(shapefile_path)
    # The merge process for county-level data will depend on state and county
    # codes. These numerical codes were stored within the US Census county 
    # shapefiles and county-level demographic data that I downloaded.
    # To help ensure that the merge process is successful, this function
    # converts the state and county codes for both tables into integer format.
    shape_data[shape_state_code_column] = shape_data[
        shape_state_code_column].astype(int)
    shape_data[shape_county_code_column] = shape_data[
        shape_county_code_column].astype(int)
    print("Simplifying shape data:") 
    shape_data['geometry'] = shape_data.simplify(tolerance = tolerance)
    print("Reading census data:")
    census_data = pd.read_csv(data_path)
    census_data[data_state_code_column] = census_data[
        data_state_code_column].astype(int)
    census_data[data_county_code_column] = census_data[
        data_county_code_column].astype(int)
    print("Merging shape and data tables:")
    merged_shape_data_table = pd.merge(shape_data, census_data, left_on = [
        shape_state_code_column, shape_county_code_column], right_on = [
            data_state_code_column, data_county_code_column])
    return merged_shape_data_table


def prepare_state_table(shapefile_path, shape_feature_name, tolerance,
data_path, data_feature_name):
    '''This function merges US Census state shapefile data with
    Census state-level demographic data in order to create a DataFrame 
    that can be used to generate choropleth maps.

    See the documentation for prepare_zip_table for more information on
    this function.'''
    print("Reading shape data:")
    shape_data = geopandas.read_file(shapefile_path)
    print("Simplifying shape data:")
    shape_data['geometry'] = shape_data.simplify(tolerance = tolerance)
    print("Reading census data:")
    census_data = pd.read_csv(data_path)
    print("Merging shape and data tables:")
    merged_shape_data_table = pd.merge(shape_data, census_data, 
    left_on = shape_feature_name, right_on = data_feature_name)
    return merged_shape_data_table



def generate_map(merged_data_table, shape_feature_name, 
    data_variable, feature_text, map_name, html_save_path, 
    screenshot_save_path, data_variable_text = 'Value',
    popup_variable_text = 'Value',  variable_decimals = 4, 
    fill_color = 'Blues', rows_to_map = 0, bin_count = 8, 
    bin_type = 'percentiles', tiles = 'Stamen Toner', generate_image = True,
    multiply_data_by = 1, vertical_legend = False, path_to_legends = ''):
    '''
    This function uses a merged data table created through prepare_zip_table,
    prepare_county_table, or prepare_zip_table to generate an interactive
    choropleth map in .html format. It then generates a .png version of 
    the map.

    Explanations of variables:

    merged_data_table: The merged data table created via prepare_zip_table,
    prepare_county_table, or prepare_zip_table

    shape_feature_name: The name of the column within the GeoDataFrame 
    containing unique IDs for each feature. It's very important that these are
    unique, as otherwise, values from one feature (e.g. a given Monroe County)
    may get copied onto other features with the same name (e.g. one of the
    other 16 Monroe Counties in the US). For counties, I recommend passing a
    column with values in (County, State) format to this argument 
    so that the map is more readable.

    data_variable: The name of the column containing the variable of interest
    (income, education level, etc.) to be graphed.

    feature_text: A string representing how the shape should be represented
    textually within the map.
    Examples would include "county", "zip", or "state."

    map_name: The string that will be used as the map's name when saving
    the .html and .png versions of the map.

    html_save_path: The path to the folder in which the .html version of the 
    map should be saved. This may need to be an absolute path, as 
    I encountered errors using a relative path.

    Important note: If you choose to use vertical legends, 
    I recommend choosing '' for the HTML save path, which ensures that the map
    will be saved in the project's root folder. This is because the vertical 
    legends sometimes wouldn't display correctly on the map if the .html image 
    was stored in a separate folder. My guess for why this occurs is that Folium
    (or another library) may expect the path to the folder containing the 
    legends to be based off the path to the folder containing the maps. For 
    instance, if your maps are in project_folder/maps, and your legends are in 
    project_folder/legends, the program may try (and fail) to find the images 
    at project_folder/maps/legends. 
    Ultimately, I recommend simply saving both the maps and the legends
    in the root folder, even if this makes your project file a bit more
    cluttered than you might like.

    screenshot_save_path: The path to the folder in which the .html 
    version of the map should be saved. This can be a relative path.

    data_variable_text: A string representing how the data variable should
    be represented textually within the map's legend.

    popup_variable_text: A string representing how the data variable should
    be represented textually within the box that displays when the user
    hovers over a given shape. It's best to keep this text short so that 
    the popup box does not become larger than necessary. For instance,
    if you're graphing median household income by county, data_variable_text
    could read "Median Household Income by County", but popup_variable_text
    can be simply "Income".

    variable_decimals: The number of decimals by which the data should be 
    rounded in the popup box.

    fill_color: The choropleth map's color pallette as sourced 
    from Color Brewer (see citation at the top of this page). 
    For color options, visit http://colorbrewer2.org/. The color code can be
    found within the URL corresponding to the color that you choose; 
    it's located in between &scheme= and &n. Examples of color codes 
    include 'RdYlGn' and 'Blues'. 
    The function will merge this fill_color string with the bins count 
    in order to import a set of colors from color_schemes_from_branca.json
    with the same length as the bins count. For example, if you select 'RdYlGn'
    as the color count and '8' as the bins count, the code will source a set
    of 8 colors from the color pallette named 'RdYlGn_08' within 
    color_schemes_from_branca.json. 
    
    rows_to_map: The number of rows in merged_data_table that should be mapped.
    If this value is set to 0, all rows will be mapped.
    Set rows_to_map to a lower amount to save rendering time when
    testing out different options.

    bin_count: The number of bins that you would like to place your 
    results into. For instance, when generating a state choropleth map,
    a bin_count of 8 will give each state one of 8 different colors
    depending on their data_variable value. 
    The maximum and minimum bin counts are based on the available
    color schemes within Color Brewer. The minimum count appears to be 3,
    whereas the maximum differs depending on the pallette type. For 
    instance, 'RdYlGn' supports up to 10 colors (and, therefore, a bin_count
    of 8), whereas 'Blues' supports a maxmimum of 9 colors.

    bin_type: The type of data bins used in the map's legend. The two options
    are 'percentiles' and 'equally_spaced.' equally_spaced is meant to 
    resemble the default bins option in Folium's choropleth map class,
    and creates bins of equal dimensions. Meanwhile, percentiles creates
    bins based on various equally spaced percentile points. You can experiment
    with both bin types to determine which option is best for your data.
    If outliers are present in your data, percentile-based bins may be ideal,
    as the color bins can otherwise be skewed by the outliers.

    tiles: The map data that you wish to use.
    I like Stamen Toner because its white/black format doesn't interfere with
    choropleth maps and because the map data is licensed under CC-BY, but
    you can insert a different tile provider if you wish. Some additional
    options are listed at:
    https://deparkes.co.uk/2016/06/10/folium-map-tiles/ 

    generate_image: Specifies whether a .png version of the map should also
    be created. You can set it to false if you are having issues getting
    the Selenium code to work on your computer or if you don't need to get
    a screenshot of the map.

    multiply_data_by: The value by which the data should be multiplied prior to
    plotting the map. A value of 100, for example, will convert proportions to
    percents, whereas a value of 0.001 will convert a median income of 50,000
    to a value of 50.000. Tweaking this variable can help make the legend
    easier to read.
   
    vertical_legend: A boolean representing whether you wish to create a 
    vertically oriented legend as opposed to a horizontally oriented one.
    I find vertical legends to be more readable than horizontal ones in 
    certain circumstances (e.g. if you have a percentile-based legend with
    long value numbers).

    path_to_legends: The path in which you wish to store .svg outputs of your
    vertical legends. I recommend keeping this at '' (e.g. the same path as
    your root folder) for simplicity's sake.

    Note: a sizeable portion of the following code, particularly the custom 
    choropleth mapping function and the code for the interactive overlay, 
    came from Amodiovalerio Verde's excellent interactive
    choropleth tutorial at
    https://vverde.github.io/blob/interactivechoropleth.html .
    Amodiovalerio informed me via email that there are "no specific
    licences for the code of interactivechoropleth. 
    You're free to use the code. A mention/link will be appreciated."
    Thank you, Amodiovalerio!


    An earlier version of this function relied heavily on the
    example choropleth code from: 
    https://python-visualization.github.io/folium/quickstart.html
    However, Amodiovalerio's code is more prominent in this version of 
    the function.

    '''

    # The function will first drop rows in the table 
    # whose data variable column value is missing.
    merged_data_table_copy = merged_data_table.copy().copy().dropna(
        subset = [data_variable]) 

    #It will then multiply all values in the data variable column by
    # the amount specified in multiply_data_by.
    merged_data_table_copy[data_variable] = merged_data_table_copy[
        data_variable]*multiply_data_by

    # Next, the values will get rounded by the value specified
    # in variable_decimals.
    merged_data_table_copy[data_variable] = round(
        merged_data_table_copy[data_variable], variable_decimals) 
        # Rounds the data to be mapped. This needs to be
        # executed before the bins are calculated below in order to avoid
        # errors in which some data falls outside the bin dimensions.

    # merged_data_table_copy['Tooltip'] = [merged_data_table_copy[shape_feature_name][i] + ": " + str(merged_data_table_copy[data_variable]) for i in range(len(merged_data_table_copy))]


    # The following lines limit the data to be mapped if a limit was entered
    # into the rows_to_map parameter. 
    if rows_to_map != 0: # A value of 0 means that all rows will be mapped.
        merged_data_table_copy = merged_data_table_copy.copy()[0:rows_to_map]
    #print("Rows to plot:",len(merged_data_table_copy))

    # Next, the bins for the map will be calculated. These bins can either
    # be percentile-based or equally spaced. In either case, bin_count is 
    # used to determine the number of bins into which the data will fall.

    if bin_type == 'percentiles':
        # First, a list of percentiles (e.g. [0, 25, 50, 75, 100] will be
        # calculated.]
        quant_bins = list(np.arange(0, 101, 100/bin_count))
        # 101 is used instead of 100 so that the 100th percentile will also
        # be included in these bins.

        bins = np.percentile(merged_data_table_copy[data_variable].dropna(), 
        quant_bins)
        # print("Bins at this point:",bins)
        # https://numpy.org/doc/stable/reference/generated/numpy.percentile.html
    # This option creates bins that correspond to different percentiles
    # of the data.

    elif bin_type == 'equally_spaced':
        min_val = merged_data_table_copy[data_variable].min()
        max_val = merged_data_table_copy[data_variable].max()
        increment = (max_val - min_val)/bin_count
        bins = list(np.arange(min_val, max_val, increment))
        bins.append(max_val)
   
    else:
        raise TypeError('Error: bin type not recognized. Bin type should be \
either \'percentiles\' or \'equally spaced.\'')

    # Next, the color scheme for the map will get loaded into the project.

    with open('color_schemes_from_branca.json') as file:
        color_file = file.read()
    # https://docs.python.org/3/tutorial/inputoutput.html

    color_dict = dict(json.loads(color_file))
    # https://docs.python.org/3/library/json.html

    # The color scheme specified by fill_color will now get merged with 
    # the number of bins (starting with a leading 0), producing a value
    # that can be searched for within color_dict. For example, the fill_color
    # value 'RdYlGn' and the bin_count value 8 will produce a value of 
    # 'RdYlGn_08', which serves as the key for a particular list of colors
    # in color_dict.
    color_list = color_dict[fill_color+'_'+str(bin_count).zfill(2)] # E.g. RdYlGn_08
    # print("Color list:", color_list)

    # This list of colors, along with the bin count, will now be used 
    # to generate a stepped color map.
    stepped_cm = cm.StepColormap(colors = color_list, index = bins, vmin = 
    bins[0], vmax = bins[-1])
    # See https://python-visualization.github.io/branca/colormap.html#colormap
    # print("Stepped_CM values:", stepped_cm.index)
    # print("Stepped CM colors:",stepped_cm.colors)
    
    # print("Colors will be assigned based on the following bins:",bins)

    # Next, the code will generate the actual choropleth map.
    m = folium.Map(location=[38.7, -95], zoom_start=6, tiles = tiles)
    # The map starts out relatively zoomed in so that the screenshot of the 
    # map generated later will have more detail.

    # Although Folium has a choropleth library, I wasn't able to find a way
    # to disable the default legend. Therefore, I am instead using a custom
    # choropleth mapping function. Much of this function is based on 
    # Amodiovalerio Verde's code at:
    # https://vverde.github.io/blob/interactivechoropleth.html . 

    # The following function assigns a color to each shape on the map based
    # on its data_variable value. I am actually not sure how it 'knows' to
    # map this color to the geometry of each shape, since the actual shape 
    # is not specified here. My guess is that it looks for the shapefile
    # coordinate data within the 'geometry' column of merged_data_table_copy,
    # but I could be wrong. I'm just glad it works!

    style_function = lambda x: {'weight':0.5, 'color': 'black', 
    'fillColor':stepped_cm(x['properties'][data_variable]), 'fillOpacity':0.75}
    # fillOpacity is set to 0.75 so that city and state names can be viewed
    # underneath the colored shapes.


    # Next, I'll create a GeoJsonTooltip object that will display the region
    # name and data value for that region when the user hovers over it.
    tooltip = folium.features.GeoJsonTooltip(fields=[shape_feature_name,data_variable], aliases = [feature_text, popup_variable_text])
    # See https://python-visualization.github.io/folium/modules.html#folium.features.GeoJsonTooltip
    # and https://python-visualization.github.io/folium/modules.html#folium.features.GeoJson

    geojson_object = folium.features.GeoJson(merged_data_table_copy, 
    style_function = style_function, tooltip = tooltip)



    geojson_object.add_to(m)

    

    # The following code presents an alternate method of generating the
    # GeoJsonTooltip objects. It comes from Amodiovalerio Verde.

    # style_function = lambda x: {'fillColor': '#ffffff', 
    #                             'color':'#000000', 
    #                             'fillOpacity': 0.0, 
    #                             'weight': 0.0}
    # highlight_function = lambda x: {'fillColor': '#000000', 
    #                                 'color':'#000000', 
    #                                 'fillOpacity': 0.50, 
    #                                 'weight': 0.1}
    # data_popup = folium.features.GeoJson(
    #     merged_data_table_copy,
    #     style_function=style_function, 
    #     control=False,
    #     highlight_function=highlight_function, 
    #     tooltip=folium.features.GeoJsonTooltip(
    #         fields=[shape_feature_name, data_variable],
    #         aliases=[feature_text, popup_variable_text],
    #         style=("background-color: white; color: #333333; font-family: \
    #         arial; font-size: 12px; padding: 10px;") 
    #     )
    # )
    # m.add_child(data_popup)
    # m.keep_in_front(data_popup)
    # folium.LayerControl().add_to(m)

    # The function next calls create_vertical_legend to add a vertical
    # legend to the map (if requested).
    if vertical_legend == True:
        create_vertical_legend(color_list = color_list, bins = bins, 
        map_name = map_name, data_variable_text = data_variable_text, 
        path_to_legends = path_to_legends, 
        variable_decimals = variable_decimals)
        # stepped_cm.colors can be used in place of color_list, but
        # they should have the same values anyway
        # print("Loading from:",path_to_legends+map_name+'_legend.svg')
        FloatImage(path_to_legends+map_name+'_legend.svg', bottom = 20, 
        left = 85).add_to(m)
        # See https://github.com/python-visualization/folium/blob/main/examples/FloatImage.ipynb
        # Although the example code uses a URL, FloatImage also works with 
        # locally stored .png and .svg files (and perhaps other image types
        # as well). Note, however, that legends added by FloatImage may not
        # display correctly within your Jupyter notebook (but they should
        # show up within the .html version of the notebook, provided that 
        # you chose compatible file paths for your maps and legends; see 
        # above notes for more details).
    
    # If a vertical legend is not requested, the map instead adds the stepped
    # colormap created earlier as the legend.
    else:
        stepped_cm.caption = data_variable_text
        stepped_cm.add_to(m)


    m.save(html_save_path+'\\'+map_name+'.html')


    if generate_image == True:

        # Finally, the function uses the Selenium library to create a screenshot 
        # of the map so that it can be shared as a .png file.
        # See https://www.selenium.dev/documentation/ for more information on 
        # Selenium. Note that some setup work is required for the Selenium code
        # to run correctly; if you don't have time right now to complete this 
        # setup, you can skip the screenshot generation process.


        ff_driver = webdriver.Firefox() 
        # See https://www.selenium.dev/documentation/webdriver/getting_started/open_browser/
        # For more information on using Selenium to get screenshots of .html 
        # files, see my get_screenshots.ipynb file within my route_maps_builder
        # program, available here:
        # https://github.com/kburchfiel/route_maps_builder/blob/master/get_screenshots.ipynb
        window_width = 3000 # This produces a large window that can better
        # capture small details (such as zip code shapefiles).
        ff_driver.set_window_size(window_width,window_width*(9/16)) # Creates
        # a window with an HD/4K/8K aspect ratio

        ff_driver.get(html_save_path+'\\'+map_name+'.html') 
        # See https://www.selenium.dev/documentation/webdriver/browser/navigation/
        time.sleep(2) # This gives the page sufficient
        # time to load the map tiles before the screenshot is taken. 
        # You can also experiment with longer sleep times.

        screenshot_image = ff_driver.get_screenshot_as_file(
            screenshot_save_path+'\\'+map_name+'.png') 
        # Based on:
        # https://www.selenium.dev/selenium/docs/api/java/org/openqa/selenium/TakesScreenshot.html

        ff_driver.quit()
        # Based on: https://www.selenium.dev/documentation/webdriver/browser/windows/

    return m


def old_generate_map(merged_data_table, shape_feature_name, 
    data_variable, feature_text, map_name, html_save_path, 
    screenshot_save_path, data_variable_text = 'Value',
    popup_variable_text = 'Value',  variable_decimals = 4, 
    fill_color = 'Blues', rows_to_map = 0, bin_type = 'percentiles', 
    tiles = 'Stamen Toner', generate_image = True, multiply_data_by = 1):
    '''
    This is an older version of generate_map that uses Folium's
    choropleth function. It doesn't accommodate vertical text legends. See
    notes within generate_map for more details regarding this function.
    '''

    merged_data_table_copy = merged_data_table.copy()

    # Much of the following code is based on the choropleth example at:
    # https://python-visualization.github.io/folium/quickstart.html

    merged_data_table_copy[data_variable] = merged_data_table_copy[
        data_variable]*multiply_data_by

    merged_data_table_copy[data_variable] = merged_data_table_copy[
        data_variable].round(
        variable_decimals) # Rounds the data to be mapped. This needs to be
        # executed before the bins are calculated below in order to avoid
        # errors in which some data falls outside the bin dimensions.


    # The following lines limit the data to be mapped if a limit was entered
    # into the rows_to_map parameter. 
    if rows_to_map != 0: # A value of 0 means that all rows will be mapped.
        merged_data_table_copy = merged_data_table_copy.copy()[0:rows_to_map]
    print("Length of table is",len(merged_data_table_copy))

    if bin_type == 'percentiles':
        bins = np.percentile(merged_data_table_copy[data_variable].dropna(), 
        [0, 12.5, 25, 37.5, 50, 62.5, 75, 87.5, 100])
        # https://numpy.org/doc/stable/reference/generated/numpy.percentile.html
    # This option creates bins that correspond to different percentiles
    # of the data.


    if bin_type == 'equally_spaced':
        min_val = merged_data_table_copy[data_variable].min()
        max_val = merged_data_table_copy[data_variable].max()
        increment = (max_val - min_val)/8
        bins = list(np.arange(min_val, max_val, increment))
        bins.append(max_val)
        print(bins)
    # This option creates equally spaced bins. If outliers are skewing the 
    # data, this option may not be as ideal as the percentiles one.

    m = folium.Map(location=[38.7, -95], zoom_start=6, tiles = tiles)
    # The latitude and longitude were chosen so that, when a screenshot of 
    # the map was taken within Firefox via the code below, the legend and 
    # data labels would be on a relatively light surface within Candada.
    folium.Choropleth(
        geo_data=merged_data_table_copy,
        name="choropleth",
        data=merged_data_table_copy,
        columns=[shape_feature_name, data_variable],
        key_on="feature.properties."+shape_feature_name,
        # See the following page for more information on folium.Choropleth
        # and other folium features:
        # https://github.com/python-visualization/folium/blob/main/folium/features.py)        
        # I believe that the values stored in the list passed to the key_on 
        # parameter must equal those stored in the first entry within the 
        # columns parameter. That's why shape_feature_name is used for 
        # both entries here.
        fill_color = fill_color,
        bins = bins,
        fill_opacity=0.75, # Allows city names to be read underneath zip codes
        line_opacity=0.2, # Without outlines, it's harder to distinguish terrain 
        # from zip codes.
        legend_name=data_variable_text
    ).add_to(m)

    folium.LayerControl().add_to(m)

    # Next, I'll add overlays that display the name of the shape and its
    # value when the user hovers over it. 

    # The following code came from Amodiovalerio Verde's excellent interactive
    # choropleth tutorial at
    # https://vverde.github.io/blob/interactivechoropleth.html .
    # Amodiovalerio informed me via email that there are "no specific
    # licences for the code of interactivechoropleth. 
    # You're free to use the code. A mention/link will be appreciated."
    # Thank you, Amodiovalerio!


    style_function = lambda x: {'fillColor': '#ffffff', 
                                'color':'#000000', 
                                'fillOpacity': 0.1, 
                                'weight': 0.1}
    highlight_function = lambda x: {'fillColor': '#000000', 
                                    'color':'#000000', 
                                    'fillOpacity': 0.50, 
                                    'weight': 0.1}
    data_popup = folium.features.GeoJson(
        merged_data_table_copy,
        style_function=style_function, 
        control=False,
        highlight_function=highlight_function, 
        tooltip=folium.features.GeoJsonTooltip(
            fields=[shape_feature_name, data_variable],
            aliases=[feature_text, popup_variable_text],
            style=("background-color: white; color: #333333; font-family: \
            arial; font-size: 12px; padding: 10px;") 
        )
    )
    m.add_child(data_popup)
    m.keep_in_front(data_popup)
    folium.LayerControl().add_to(m)

    # Note: A simpler means of adding a tooltip to the map would look something like the following. [I haven't tested out this code within this function, however.]

    #     tooltip = folium.features.GeoJsonTooltip(fields = [shape_feature_name, data_variable], aliases = [feature_text, popup_variable_text)
    # # Based on https://python-visualization.github.io/folium/modules.html#folium.features.GeoJsonTooltip

    # folium.features.GeoJson(data = merged_data_table_copy, tooltip=tooltip, style_function = lambda x:{'opacity':0, 'fillOpacity':0}).add_to(m)

    # # Style function parameters come from https://leafletjs.com/SlavaUkraini/reference.html#path ; the format of style_function is based on one of the examples on https://python-visualization.github.io/folium/modules.html#folium.features.GeoJsonTooltip

    m.save(html_save_path+'\\'+map_name+'.html')


    # Finally, the function uses the Selenium library to create a screenshot 
    # of the map so that it can be shared as a .png file.
    # See https://www.selenium.dev/documentation/ for more information on 
    # Selenium. Note that some setup work is required for the Selenium code
    # to run correctly; if you don't have time right now to complete this 
    # setup, you can skip the screenshot generation process.

    if generate_image == True:

        ff_driver = webdriver.Firefox() 
        # See https://www.selenium.dev/documentation/webdriver/getting_started/open_browser/
        # For more information on using Selenium to get screenshots of .html 
        # files, see my get_screenshots.ipynb file within my route_maps_builder
        # program, available here:
        # https://github.com/kburchfiel/route_maps_builder/blob/master/get_screenshots.ipynb
        window_width = 3000 # This produces a large window that can better
        # capture small details (such as zip code shapefiles).
        ff_driver.set_window_size(window_width,window_width*(9/16)) # Creates
        # a window with an HD/4K/8K aspect ratio

        ff_driver.get(html_save_path+'\\'+map_name+'.html') 
        # See https://www.selenium.dev/documentation/webdriver/browser/navigation/
        time.sleep(2) # This gives the page sufficient
        # time to load the map tiles before the screenshot is taken. 
        # You can also experiment with longer sleep times.

        screenshot_image = ff_driver.get_screenshot_as_file(
            screenshot_save_path+'\\'+map_name+'.png') 
        # Based on:
        # https://www.selenium.dev/selenium/docs/api/java/org/openqa/selenium/TakesScreenshot.html

        ff_driver.quit()
        # Based on: https://www.selenium.dev/documentation/webdriver/browser/windows/

    return m