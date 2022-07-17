def run(dirOut = "FLFFCoutput", country = "United Kingdom", steps = 50):
    # Import standard modules ...
    import os

    # Import special modules ...
    try:
        import cartopy
        import cartopy.crs
        import cartopy.io
        import cartopy.io.shapereader
    except:
        raise Exception("\"cartopy\" is not installed; run \"pip install --user Cartopy\"") from None
    try:
        import matplotlib
        matplotlib.use("Agg")                                                   # NOTE: See https://matplotlib.org/stable/gallery/user_interfaces/canvasagg.html
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
    shape_file = cartopy.io.shapereader.natural_earth(
        resolution = "10m",
        category = "cultural",
        name = "admin_0_countries"
    )

    # Loop over records ...
    for record in cartopy.io.shapereader.Reader(shape_file).records():
        # Skip this record if it is not the one we are looking for ...
        if record.attributes["NAME"] != country:
            continue

        # Find extent of the country ...
        lon_min, lat_min, lon_max, lat_max = record.bounds                      # [°], [°], [°], [°]
        print(f'The bounding box of {record.attributes["NAME"]} is from ({lon_min:.2f},{lat_min:.2f}) to ({lon_max:.2f},{lat_max:.2f}).')

        # Create plot and make it pretty ...
        fg = matplotlib.pyplot.figure(figsize = (9, 6), dpi = 300)
        ax = fg.add_subplot(projection = cartopy.crs.PlateCarree())
        ax.set_extent(
            [
                lon_min - 0.1,
                lon_max + 0.1,
                lat_min - 0.1,
                lat_max + 0.1
            ]
        )
        pyguymer3.geo.add_map_background(ax, resolution = "large8192px")
        ax.coastlines(resolution = "10m", color = "black", linewidth = 0.1)

        # Make longitude and latitude grid ...
        xcoords = numpy.linspace(lon_min, lon_max, num = steps)                 # [°]
        ycoords = numpy.linspace(lat_min, lat_max, num = steps)                 # [°]

        # Make empty lists of points ...
        xpoints = []                                                            # [°]
        ypoints = []                                                            # [°]
        zpoints = []                                                            # [m]

        # Loop over longitudes ...
        for ix in range(xcoords.size):
            print(f"Calculating slice {ix + 1:d} of {xcoords.size:d} ...")

            # Loop over latitudes ...
            for iy in range(ycoords.size):
                # Skip this point if it is not within the geometry ...
                if not record.geometry.contains(shapely.geometry.Point(xcoords[ix], ycoords[iy])):
                    continue

                # Set a silly initial minimum ...
                # NOTE: Earth's mean radius is 6,371,009 m.
                # NOTE: Therefore, Earth's mean circumference is 40,030,230 m.
                zpoint1 = 5.0e7                                                 # [m]

                # Loop over boundaries ...
                for boundary in record.geometry.boundary:
                    # Loop over coordinates ...
                    for coord in boundary.coords:
                        # Find distance between points ...
                        zpoint2, alpha1, alpha2 = pyguymer3.geo.calc_dist_between_two_locs(
                            lon1_deg = xcoords[ix],
                            lat1_deg = ycoords[iy],
                            lon2_deg = coord[0],
                            lat2_deg = coord[1]
                        )                                                       # [m], [°], [°]

                        # Replace current minimum if required ...
                        if zpoint2 < zpoint1:
                            zpoint1 = zpoint2                                   # [m]

                # Add values to lists (converting from m to km) ...
                xpoints.append(xcoords[ix])                                     # [°]
                ypoints.append(ycoords[iy])                                     # [°]
                zpoints.append(zpoint1 / 1000.0)                                # [km]

        print(f"The furthest you can get from the coast is ~{max(zpoints):.1f} km.")

        # Plot points ...
        # NOTE: Default value of the optional keyword argument "s" (as of
        #       November 2016) is "20 points ^ 2". Therefore, the nominal width/
        #       height is approximately "4.5 points" (assuming that the circles
        #       are actually sized like squares). I want to scale the width/
        #       height so that the circles do not overlap. The following tweak
        #       should do that as different users request different numbers of
        #       steps. With the default value of "steps = 50" the size will be
        #       "16 points ^ 2" - a slightly smaller area than default.
        sc = matplotlib.pyplot.scatter(
            xpoints,
            ypoints,
            s = (200 / steps) ** 2,
            c = zpoints,
            alpha = 0.5,
            linewidth = 0.5,
            cmap = matplotlib.pyplot.cm.rainbow,
            vmin = 0.0,
            transform = cartopy.crs.Geodetic()
        )

        # Add colour bar ...
        cb = matplotlib.pyplot.colorbar(sc)
        cb.set_label("Distance [km]")

        # Save map as PNG ...
        ax.set_title("Location Furthest From Coast")
        fg.savefig(
            f"{dirOut}/{country}.png",
            bbox_inches = "tight",
                    dpi = 300,
             pad_inches = 0.1
        )
        pyguymer3.image.optimize_image(f"{dirOut}/{country}.png", strip = True)
        matplotlib.pyplot.close(fg)
