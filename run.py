# -*- coding: utf-8 -*-

def run(dirOut = "FLFFCoutput", country = "United Kingdom", steps = 50):
    # Import modules ...
    import cartopy
    import cartopy.crs
    import cartopy.io
    import cartopy.io.shapereader
    import matplotlib
    # NOTE: http://matplotlib.org/faq/howto_faq.html#matplotlib-in-a-web-application-server
    matplotlib.use("Agg")
    import matplotlib.pyplot
    import numpy
    import os
    import shapely
    import shapely.geometry

    # Load sub-functions ...
    from .dist_between_two_locs import dist_between_two_locs

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
        lon_min, lat_min, lon_max, lat_max = record.bounds                      # [deg], [deg], [deg], [deg]
        print "The bounding box of {0:s} is from ({1:.2f},{2:.2f}) to ({3:.2f},{4:.2f}).".format(record.attributes["NAME"], lon_min, lat_min, lon_max, lat_max)

        # Create plot and make it pretty ...
        fig = matplotlib.pyplot.figure(
            figsize = (9, 6),
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
        xcoords = numpy.linspace(lon_min, lon_max, num = steps)                 # [deg]
        ycoords = numpy.linspace(lat_min, lat_max, num = steps)                 # [deg]

        # Make empty lists of points ...
        xpoints = []                                                            # [deg]
        ypoints = []                                                            # [deg]
        zpoints = []                                                            # [m]

        # Loop over longitudes ...
        for ix in xrange(xcoords.size):
            print "Calculating slice {0:d} of {1:d} ...".format(ix + 1, xcoords.size)

            # Loop over latitudes ...
            for iy in xrange(ycoords.size):
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
                        zpoint2, alpha1, alpha2 = dist_between_two_locs(
                            lon1_deg = xcoords[ix],
                            lat1_deg = ycoords[iy],
                            lon2_deg = coord[0],
                            lat2_deg = coord[1]
                        )                                                       # [m], [deg], [deg]

                        # Replace current minimum if required ...
                        if zpoint2 < zpoint1:
                            zpoint1 = zpoint2                                   # [m]

                # Add values to lists ...
                xpoints.append(xcoords[ix])                                     # [deg]
                ypoints.append(ycoords[iy])                                     # [deg]
                zpoints.append(zpoint1)                                         # [m]

        # Convert m to km ...
        zpoints /= 1000.0                                                       # [km]

        print "The furthest you can get from the coast is ~{0:.1f} km.".format(max(zpoints))

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
        matplotlib.pyplot.title("Location Furthest From Coast")
        matplotlib.pyplot.savefig(
            os.path.join(dirOut, "{0:s}.png".format(country)),
            dpi = 300,
            bbox_inches = "tight",
            pad_inches = 0.1
        )
        matplotlib.pyplot.close("all")
