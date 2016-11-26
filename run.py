# -*- coding: utf-8 -*-

def run(country = "United Kingdom"):
    # Import modules ...
    import cartopy.crs
    import cartopy.io.shapereader
    import numpy
    import matplotlib.pyplot
    import shapely.geometry

    # Load sub-functions ...
    from .dist_between_two_locs import dist_between_two_locs

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
        lon_min, lat_min, lon_max, lat_max = record.bounds
        print "The bounding box of {0:s} is from ({1:.2f},{2:.2f}) to ({3:.2f},{4:.2f}).".format(record.attributes["NAME"], lon_min, lat_min, lon_max, lat_max)

        # Create plot and make it pretty ...
        fig = matplotlib.pyplot.figure(
            figsize = (6, 6),
            dpi = 300,
            frameon = False
        )
        ax = matplotlib.pyplot.axes(projection = cartopy.crs.PlateCarree())
        ax.set_extent(
            [
                lon_min - 0.1,
                lon_max + 0.1,
                lat_min - 0.1,
                lat_max + 0.1
            ]
        )
        ax.stock_img()
        ax.coastlines(
            resolution = "10m",
            color = "black",
            linewidth = 0.1
        )

        # Make longitude and latitude grid ...
        xcoords = numpy.linspace(lon_min, lon_max)
        ycoords = numpy.linspace(lat_min, lat_max)

        # Make empty lists of points ...
        xpoints = []
        ypoints = []
        zpoints = []

        # Loop over longitudes ...
        for ix in xrange(xcoords.size):
            print "Calculating slice {0:d} of {1:d} ...".format(ix + 1, xcoords.size)

            # Loop over latitudes ...
            for iy in xrange(ycoords.size):
                # Skip this point if it is not within the geometry ...
                if not record.geometry.contains(shapely.geometry.Point(xcoords[ix], ycoords[iy])):
                    continue

                # Set silly minimum ...
                # NOTE: Earth's mean radius is 6,371.009 km.
                # NOTE: Therefore, Earth's mean circumference is 40,030.230 km.
                zpoint1 = 1.0e6

                # Loop over boundaries ...
                for boundary in record.geometry.boundary:
                    # Loop over coordinates ...
                    for coord in boundary.coords:
                        # Find distance between points ...
                        zpoint2 = dist_between_two_locs(
                            lon1 = xcoords[ix],
                            lat1 = ycoords[iy],
                            lon2 = coord[0],
                            lat2 = coord[1]
                        )

                        # Replace current minimum if required ...
                        if zpoint2 < zpoint1:
                            zpoint1 = zpoint2

                # Add values to lists ...
                xpoints.append(xcoords[ix])
                ypoints.append(ycoords[iy])
                zpoints.append(zpoint1)

        print "The furthest you can get from the coast is ~{0:.1f} km.".format(max(zpoints))

        # Plot points ...
        matplotlib.pyplot.scatter(
            xpoints,
            ypoints,
            c = zpoints,
            alpha = 0.5,
            linewidth = 0.5,
            cmap = matplotlib.pyplot.cm.hsv,
            vmin = 0.0,
            transform = cartopy.crs.Geodetic()
        )

        # Save map as PNG ...
        matplotlib.pyplot.title("Distance From Coast")
        matplotlib.pyplot.savefig(
            "{0:s}.png".format(country),
            dpi = 300,
            bbox_inches = "tight",
            pad_inches = 0.1
        )
        matplotlib.pyplot.close("all")
