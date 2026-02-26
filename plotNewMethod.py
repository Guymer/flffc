#!/usr/bin/env python3

# Use the proper idiom in the main module ...
# NOTE: See https://docs.python.org/3.12/library/multiprocessing.html#the-spawn-and-forkserver-start-methods
if __name__ == "__main__":
    # Import standard modules ...
    import argparse
    import gzip
    import os
    import pathlib
    import subprocess
    import sysconfig

    # Import special modules ...
    try:
        import cartopy
        cartopy.config.update(
            {
                "cache_dir" : pathlib.PosixPath("~/.local/share/cartopy").expanduser(),
            }
        )
    except:
        raise Exception("\"cartopy\" is not installed; run \"pip install --user Cartopy\"") from None
    try:
        import matplotlib
        matplotlib.rcParams.update(
            {
                       "axes.xmargin" : 0.01,
                       "axes.ymargin" : 0.01,
                            "backend" : "Agg",                                  # NOTE: See https://matplotlib.org/stable/gallery/user_interfaces/canvasagg.html
                         "figure.dpi" : 300,
                     "figure.figsize" : (9.6, 7.2),                             # NOTE: See https://github.com/Guymer/misc/blob/main/README.md#matplotlib-figure-sizes
                          "font.size" : 8,
                "image.interpolation" : "none",
                     "image.resample" : False,
            }
        )
        import matplotlib.pyplot
    except:
        raise Exception("\"matplotlib\" is not installed; run \"pip install --user matplotlib\"") from None
    try:
        import shapely
        import shapely.wkb
    except:
        raise Exception("\"shapely\" is not installed; run \"pip install --user Shapely\"") from None

    # Import my modules ...
    try:
        import pyguymer3
        import pyguymer3.geo
        import pyguymer3.image
    except:
        raise Exception("\"pyguymer3\" is not installed; run \"pip install --user PyGuymer3\"") from None

    # **************************************************************************

    # Create argument parser and parse the arguments ...
    parser = argparse.ArgumentParser(
           allow_abbrev = False,
            description = "foobar",
        formatter_class = argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--debug",
        action = "store_true",
          dest = "debug",
          help = "print debug messages",
    )
    parser.add_argument(
        "--eps",
        default = 1.0e-12,
           dest = "eps",
           help = "the tolerance of the Vincenty formula iterations",
           type = float,
    )
    parser.add_argument(
        "--nAng",
        default = 361,
           dest = "nAng",
           help = "the number of angles around each circle",
           type = int,
    )
    parser.add_argument(
        "--nIter",
        default = 1000000,
           dest = "nIter",
           help = "the maximum number of iterations (particularly the Vincenty formula)",
           type = int,
    )
    parser.add_argument(
        "--thunderforest-key",
        default = None,
           dest = "thunderforestKey",
           help = "the API key for Thunderforest",
           type = str,
    )
    parser.add_argument(
        "--thunderforest-map",
        default = "atlas",
           dest = "thunderforestMap",
           help = "the name of the Thunderforest map to use (see https://www.thunderforest.com/maps/)",
           type = str,
    )
    parser.add_argument(
        "--tile-scale",
        default = 1,
           dest = "tileScale",
           help = "scale of the tiles",
           type = int,
    )
    parser.add_argument(
        "--timeout",
        default = 60.0,
           help = "the timeout for any requests/subprocess calls (in seconds)",
           type = float,
    )
    parser.add_argument(
        "--tolerance",
        default = 1.0e-10,
           dest = "tol",
           help = "the Euclidean distance that defines two points as being the same (in degrees)",
           type = float,
    )
    args = parser.parse_args()

    # **************************************************************************

    # Create short-hands ...
    fill = 1.0e3                                                                # [m]
    maxDists = [
        250,
         50,
         10,
          2,
    ]                                                                           # [km]
    midLat = 61.637344                                                          # [°]
    midLon = 12.827752                                                          # [°]
    simp = 100.0 / pyguymer3.RESOLUTION_OF_EARTH                                # [°]

    # Create short-hands ...
    pnt = shapely.geometry.point.Point(midLon, midLat)
    fovs = [
        pyguymer3.geo.buffer(
            pnt,
            float(1000 * maxDist),
            debug = args.debug,
              eps = args.eps,
             fill = -1.0,
             nAng = 361,
            nIter = args.nIter,
             simp = -1.0,
              tol = args.tol,
        ) for maxDist in maxDists
    ]

    # **************************************************************************

    # Create figure ...
    fg = matplotlib.pyplot.figure(figsize = (len(maxDists) * 7.2, 7.2))

    # Create axis ...
    axs = [
        pyguymer3.geo.add_axis(
            fg,
            add_coastlines = False,
             add_gridlines = True,
                     debug = args.debug,
                      dist = float(1000 * maxDist),
                       eps = args.eps,
                       fov = fov,
                     index = i + 1,
                       lat = midLat,
                       lon = midLon,
                     ncols = len(maxDists),
                     nIter = args.nIter,
                     nrows = 1,
                       tol = args.tol,
        ) for i, (fov, maxDist) in enumerate(zip(fovs, maxDists, strict = True))
    ]

    # Calculate the regrid shape based off the resolution and the size of the
    # figure, as well as a safety factor (remembering Nyquist) ...
    regrid_shape = (
        round(2.0 * fg.get_figwidth() * fg.get_dpi() / float(len(maxDists))),
        round(2.0 * fg.get_figheight() * fg.get_dpi()),
    )                                                                           # [px], [px]

    # Calculate the resolution depending on the half-width, or the half-height,
    # of the figure and the maximum distance, as well as a safety factor
    # (remembering Nyquist) ...
    ress = [
        2.0 * min(
            2.0 * float(1000 * maxDist) / (fg.get_figwidth() * fg.get_dpi() / float(len(maxDists))),
            2.0 * float(1000 * maxDist) / (fg.get_figheight() * fg.get_dpi()),
        ) for maxDist in maxDists
    ]                                                                           # [m/px]

    # Add OSM tiles background using Cartopy ...
    for ax, res in zip(axs, ress, strict = True):
        pyguymer3.geo.add_Cartopy_tiles(
            ax,
            midLat,
            res,
                       debug = args.debug,
               interpolation = "gaussian",
                regrid_shape = regrid_shape,
            thunderforestKey = args.thunderforestKey,
            thunderforestMap = args.thunderforestMap,
                   tileScale = args.tileScale,
                           z = None,
        )

    # **************************************************************************

    # Loop over GSHHG resolutions ...
    for iGshhgRes, gshhgRes in enumerate(
        [
            "c",                        # crude
            "l",                        # low
            "i",                        # intermediate
            "h",                        # high
            "f",                        # full
        ]
    ):
        print(f"Processing GSHHG resolution \"{gshhgRes}\" ...")

        # Create short-hand ...
        dName1 = f"newOutput/gshhgRes={gshhgRes}"

        # Loop over distances ...
        for dist in range(50, 250 + 2, 2):
            print(f"  Processing distance {dist:d} km ...")

            # Create short-hands and skip if the WKB is missing ...
            dName2 = f"{dName1}/eps={args.eps:.2e}_fill={fill:.2e}_nAng={args.nAng:d}_nIter={args.nIter:d}_simp={simp:.2e}_tol={args.tol:.2e}"
            done = False
            wName = f"{dName2}/dist={dist:03d}km.wkb.gz"
            if not os.path.exists(wName):
                continue

            # Load Polygons ...
            # NOTE: Given how the Polygons were made, we know that there aren't
            #       any invalid Polygons, so don't bother checking for them.
            with gzip.open(wName, mode = "rb") as gzObj:
                polys = pyguymer3.geo.extract_polys(
                    shapely.wkb.loads(gzObj.read()),
                    onlyValid = False,
                       repair = False,
                )

            # Loop over sub-plots ...
            for ax, fov in zip(axs, fovs, strict = True):
                # Create a subset of Polygons which contain the Point ...
                relevantPolys = []
                for poly in polys:
                    if poly.contains(pnt):
                        relevantPolys.append(poly.intersection(fov))

                # Skip this distance if there aren't any Polygons ...
                match len(relevantPolys):
                    case 0:
                        print(f"    There aren't any Polygons which are relevant - stopping looping over distance.")

                        # Set flag ...
                        done = True
                    case 1:
                        print(f"    The centroid is at ({relevantPolys[0].centroid.x:.6f}°,{relevantPolys[0].centroid.y:.6f}°).")

                        # Plot Polygon ...
                        ax.add_geometries(
                            relevantPolys,
                            cartopy.crs.PlateCarree(),
                            edgecolor = f"C{iGshhgRes:d}",
                            facecolor = "none",
                            linewidth = 1.0,
                        )
                    case _:
                        raise Exception(f"there are {len(relevantPolys):,d} Polygons which are relevant") from None
                del relevantPolys
            del polys

            # Stop looping if done ...
            if done:
                break

    # Plot the starting location ...
    # NOTE: As of 5/Dec/2023, the default "zorder" of the coastlines is 1.5, the
    #       default "zorder" of the gridlines is 2.0 and the default "zorder" of
    #       the scattered points is 1.0.
    for ax in axs:
        ax.scatter(
            [midLon],
            [midLat],
            edgecolor = "black",
            facecolor = "gold",
               marker = "*",
            transform = cartopy.crs.Geodetic(),
               zorder = 5.0,
        )

    # Configure axis ...
    for ax, maxDist in zip(axs, maxDists, strict = True):
        ax.set_title(f"{maxDist:d} km")

    # Configure figure ...
    fg.suptitle(f"({midLon:.6f}°,{midLat:.6f}°)")
    fg.tight_layout()

    # Save figure ...
    fg.savefig("plotNewMethod.png")
    matplotlib.pyplot.close(fg)

    # Optimize PNG ...
    pyguymer3.image.optimise_image(
        "plotNewMethod.png",
          debug = args.debug,
          strip = True,
        timeout = args.timeout,
    )
