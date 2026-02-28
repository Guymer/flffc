#!/usr/bin/env python3

# Use the proper idiom in the main module ...
# NOTE: See https://docs.python.org/3.12/library/multiprocessing.html#the-spawn-and-forkserver-start-methods
if __name__ == "__main__":
    # Import standard modules ...
    import argparse
    import copy
    import json
    import os
    import pathlib

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
        raise Exception("\"pyguymer3\" is not installed; run \"pip install --user PyGuymer3\"") from None

    # **************************************************************************

    # Create argument parser and parse the arguments ...
    parser = argparse.ArgumentParser(
           allow_abbrev = False,
            description = "Demonstrate the scope of a potential new method.",
        formatter_class = argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--debug",
        action = "store_true",
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
        "--fill-factor",
        default = 0.01,
           dest = "fillFact",
           help = "the multiplication factor to fill shapes by, relative to the buffering distance",
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
        "--RAM-limit",
        default = 1073741824,
           dest = "ramLimit",
           help = "the maximum RAM usage of each \"large\" array (in bytes)",
           type = int,
    )
    parser.add_argument(
        "--timeout",
        default = 60.0,
           help = "the timeout for any requests/subprocess calls (in seconds)",
           type = float,
    )
    args = parser.parse_args()

    # **************************************************************************

    # Create short-hands ...
    maxArea = 1.0e15                                                            # [m2]
    maxLength = 1.0e9                                                           # [m]
    minArea = 1.0e2                                                             # [m2]
    minLength = 1.0e1                                                           # [m]
    nPoint = round(float(args.ramLimit) / float(args.nAng * 2 * 8))             # [#]
    onlyValid = True
    repair = True

    # **************************************************************************

    print(f"You have specified a fill factor of ×{args.fillFact:.2e}.")
    print(f"You have specified a RAM limit of {args.ramLimit:,d} bytes.")
    print(f"You have specified that there are {args.nAng:,d} angles.")
    print(f"Therefore, you can only have up to {nPoint:,d} points in a CoordinateSequence.")

    # Create figure ...
    fg = matplotlib.pyplot.figure()

    # Create axis ...
    ax = fg.add_subplot()

    # Loop over GSHHG resolutions ...
    for gshhgRes in [
        "c",                            # crude
        "l",                            # low
        "i",                            # intermediate
        "h",                            # high
        "f",                            # full
    ]:
        print(f"Surveying \"{gshhgRes}\" ...")

        # Create short-hands and make output folder if it is missing ...
        dName = f"newOutput/gshhgRes={gshhgRes}"
        jName1 = f"{dName}/areas.json"
        jName2 = f"{dName}/lengths.json"
        if not os.path.exists(dName):
            os.makedirs(dName)

        # Check if the JSONs have already been made ...
        if os.path.exists(jName1) and os.path.exists(jName2):
            print("  Loading JSONs ...")

            # Load lists ...
            with open(jName1, "rt", encoding = "utf-8") as fObj:
                areas = json.load(fObj)                                         # [m2]
            with open(jName2, "rt", encoding = "utf-8") as fObj:
                lengths = json.load(fObj)                                       # [m]

            # Check data ...
            assert isinstance(areas, list)
            assert isinstance(lengths, list)
            assert len(areas) == len(lengths)
        else:
            # Initialize lists ...
            areas = []                                                          # [m2]
            lengths = []                                                        # [m]

            # Loop over records in the GSHHG Shapefile for the boundary between
            # land and ocean at this resolution ...
            for record in cartopy.io.shapereader.Reader(
                cartopy.io.shapereader.gshhs(
                    level = 1,
                    scale = gshhgRes,
                )
            ).records():
                # Skip bad records ...
                if not hasattr(record, "geometry"):
                    continue

                # Loop over Polygons in record ...
                for poly in pyguymer3.geo.extract_polys(
                    record.geometry,
                    onlyValid = onlyValid,
                       repair = repair,
                ):
                    # Append values to lists ...
                    areas.append(
                        round(
                            pyguymer3.geo.area(
                                poly,
                                       eps = args.eps,
                                     level = 1,
                                     nIter = args.nIter,
                                 onlyValid = onlyValid,
                                    repair = repair,
                                splitSpace = "EuclideanSpace",
                            )
                        )
                    )                                                           # [m2]
                    lengths.append(
                        round(
                            pyguymer3.geo.length(
                                poly.exterior,
                                      eps = args.eps,
                                    nIter = args.nIter,
                                onlyValid = onlyValid,
                            )
                        )
                    )                                                           # [m]

            print("  Saving JSONs ...")

            # Save lists ...
            with open(jName1, "wt", encoding = "utf-8") as fObj:
                json.dump(
                    areas,
                    fObj,
                    ensure_ascii = False,
                          indent = 4,
                       sort_keys = True,
                )
            with open(jName2, "wt", encoding = "utf-8") as fObj:
                json.dump(
                    lengths,
                    fObj,
                    ensure_ascii = False,
                          indent = 4,
                       sort_keys = True,
                )

        # Plot lists ...
        ax.scatter(
            areas,
            lengths,
            label = f"gshhgRes={gshhgRes}",
        )

        # **************************************************************************

        # Create short-hands ...
        maxLengths = max(lengths)                                               # [m]
        minFill = float(maxLengths) / float(nPoint - 1)                         # [m]

        print(f"  The longest coastline is {maxLengths:,d} metres.")
        print(f"  Therefore, you can only fill every {minFill:,.1f} metres.")
        print(f"  Therefore, you can only buffer every {minFill / args.fillFact:,.1f} metres.")

    # Shade impossible region ...
    a = numpy.pow(
        10,
        numpy.linspace(
            numpy.log10(minArea),
            numpy.log10(maxArea),
            num = 100,
        ),
    )                                                                           # [m2]
    c = 2.0 * numpy.pi * numpy.sqrt(a / numpy.pi)                               # [m]
    numpy.place(c, a >= pyguymer3.SURFACE_AREA_OF_EARTH, maxLength)             # [m]
    ax.fill_between(
        a,
        c,
            alpha = 0.25,
        edgecolor = "none",
        facecolor = "red",
            label = "impossible",
    )

    # Configure axis ...
    ax.grid()
    ax.legend(loc = "lower right")
    ax.semilogx()
    ax.semilogy()
    ax.set_aspect("equal")
    ax.set_title("How long is the LinearRing around each Polygon?")
    ax.set_xlabel("Geodesic Area [m²]")
    ax.set_xlim(minArea, maxArea)
    ax.set_xticks(
        [
            pow(10, i) for i in range(
                round(numpy.log10(minArea)),
                round(numpy.log10(maxArea)) + 1,
            )
        ]
    )
    ax.set_ylabel("(Exterior) Geodesic Length [m]")
    ax.set_ylim(minLength, maxLength)
    ax.set_yticks(
        [
            pow(10, i) for i in range(
                round(numpy.log10(minLength)),
                round(numpy.log10(maxLength)) + 1,
            )
        ]
    )

    # Configure figure ...
    fg.tight_layout()

    # Save figure ...
    fg.savefig("newMethodScope.png")
    matplotlib.pyplot.close(fg)

    # Optimize PNG ...
    pyguymer3.image.optimise_image(
        "newMethodScope.png",
          debug = args.debug,
          strip = True,
        timeout = args.timeout,
    )
