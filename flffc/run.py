#!/usr/bin/env python3

# Define function ...
def run(dirOut, /, *, country = "United Kingdom", steps = 50):
    # Import standard modules ...
    import os

    # Import special modules ...
    try:
        import cartopy
        cartopy.config.update(
            {
                "cache_dir" : os.path.expanduser("~/.local/share/cartopy_cache"),
            }
        )
    except:
        raise Exception("\"cartopy\" is not installed; run \"pip install --user Cartopy\"") from None
    try:
        import matplotlib
        matplotlib.rcParams.update(
            {
                       "backend" : "Agg",                                       # NOTE: See https://matplotlib.org/stable/gallery/user_interfaces/canvasagg.html
                    "figure.dpi" : 300,
                "figure.figsize" : (9.6, 7.2),                                  # NOTE: See https://github.com/Guymer/misc/blob/main/README.md#matplotlib-figure-sizes
                     "font.size" : 8,
            }
        )
        import matplotlib.pyplot
    except:
        raise Exception("\"matplotlib\" is not installed; run \"pip install --user matplotlib\"") from None
    try:
        import numpy
    except:
        raise Exception("\"numpy\" is not installed; run \"pip install --user numpy\"") from None
    try:
        import shapely
        import shapely.geometry
    except:
        raise Exception("\"shapely\" is not installed; run \"pip install --user Shapely\"") from None

    # Import my modules ...
    try:
        import pyguymer3
        import pyguymer3.geo
        import pyguymer3.image
    except:
        raise Exception("\"pyguymer3\" is not installed; you need to have the Python module from https://github.com/Guymer/PyGuymer3 located somewhere in your $PYTHONPATH") from None

    # Make output directory ...
    if not os.path.exists(dirOut):
        os.makedirs(dirOut)

    # Find file containing all the country shapes ...
    sfile = cartopy.io.shapereader.natural_earth(
          category = "cultural",
              name = "admin_0_countries",
        resolution = "10m",
    )

    # Loop over records ...
    for record in cartopy.io.shapereader.Reader(sfile).records():
        # Create short-hand ...
        neName = pyguymer3.geo.getRecordAttribute(record, "NAME")

        # Skip this record if it is not the one we are looking for ...
        if neName != country:
            continue

        # Find extent of the country ...
        lon_min, lat_min, lon_max, lat_max = record.bounds                      # [°], [°], [°], [°]
        print(f"The bounding box of {neName} is from ({lon_min:.2f}°,{lat_min:.2f}°) to ({lon_max:.2f}°,{lat_max:.2f}°).")

        # Make longitude and latitude grid ...
        xcoords = numpy.linspace(lon_min, lon_max, num = steps)                 # [°]
        ycoords = numpy.linspace(lat_min, lat_max, num = steps)                 # [°]

        # Make empty lists of points ...
        xpoints = []                                                            # [°]
        ypoints = []                                                            # [°]
        zpoints = []                                                            # [m]

        # Loop over longitudes ...
        for ix in range(steps):
            print(f"Calculating slice {ix + 1:d} of {steps:d} ...")

            # Loop over latitudes ...
            for iy in range(steps):
                # Skip this point if it is not within the geometry ...
                if not record.geometry.contains(shapely.geometry.Point(xcoords[ix], ycoords[iy])):
                    continue

                # Set a silly initial minimum ...
                zpoint1 = 2.0 * pyguymer3.CIRCUMFERENCE_OF_EARTH                # [m]

                # Loop over Polygons ...
                for poly in pyguymer3.geo.extract_polys(record.geometry):
                    # Loop over coordinates in exterior ring ...
                    for coord in poly.exterior.coords:
                        # Find distance between points ...
                        zpoint2, _, _ = pyguymer3.geo.calc_dist_between_two_locs(
                            xcoords[ix],
                            ycoords[iy],
                            coord[0],
                            coord[1],
                        )                                                       # [m], [°], [°]

                        # Replace current minimum if required ...
                        if zpoint2 < zpoint1:
                            zpoint1 = zpoint2                                   # [m]

                # Add values to lists (converting from m to km) ...
                xpoints.append(xcoords[ix])                                     # [°]
                ypoints.append(ycoords[iy])                                     # [°]
                zpoints.append(zpoint1 / 1000.0)                                # [km]

        print(f"The furthest you can get from the coast is ~{max(zpoints):.1f} km.")

        # Find middle of points and the furthest distance ...
        midLon, midLat, maxDist = pyguymer3.geo.find_middle_of_locs(
            numpy.array(xpoints),
            numpy.array(ypoints),
            pad = 12.0 * 1852.0,
        )                                                                       # [°], [°], [m]

        # Create figure ...
        fg = matplotlib.pyplot.figure()

        # Create axis ...
        ax = pyguymer3.geo.add_axis(
            fg,
            dist = maxDist,
             lat = midLat,
             lon = midLon,
        )

        # Configure axis ...
        pyguymer3.geo.add_coastlines(ax)
        pyguymer3.geo.add_map_background(ax, resolution = "large8192px")

        # Plot points ...
        # NOTE: Default value of the optional keyword argument "s" (as of
        #       November 2016) is "20 points ^ 2". Therefore, the nominal width/
        #       height is approximately "4.5 points" (assuming that the circles
        #       are actually sized like squares). I want to scale the width/
        #       height so that the circles do not overlap. The following tweak
        #       should do that as different users request different numbers of
        #       steps. With the default value of "steps = 50" the size will be
        #       "16 points ^ 2" - a slightly smaller area than default.
        # NOTE: As of 5/Dec/2023, the default "zorder" of the coastlines is 1.5,
        #       the default "zorder" of the gridlines is 2.0 and the default
        #       "zorder" of the scattered points is 1.0.
        sc = ax.scatter(
            xpoints,
            ypoints,
                    c = zpoints,
                 cmap = matplotlib.pyplot.cm.rainbow,
            linewidth = 0.5,
                    s = pow(200.0 / steps, 2),
            transform = cartopy.crs.Geodetic(),
                 vmin = 0.0,
               zorder = 5.0,
        )

        # Add colour bar ...
        cb = fg.colorbar(sc, ax = ax, orientation = "vertical")

        # Configure colour bar ...
        cb.set_label("Distance [km]")

        # Configure axis ...
        ax.set_title("Location Furthest From Coast")

        # Configure figure ...
        fg.tight_layout()

        # Save figure ...
        fg.savefig(f"{dirOut}/{country}.png")
        matplotlib.pyplot.close(fg)

        # Optimize PNG ...
        pyguymer3.image.optimize_image(
            f"{dirOut}/{country}.png",
            strip = True,
        )
