#!/usr/bin/env python3

# Use the proper idiom in the main module ...
# NOTE: See https://docs.python.org/3.12/library/multiprocessing.html#the-spawn-and-forkserver-start-methods
if __name__ == "__main__":
    # Import standard modules ...
    import argparse
    import copy
    import gzip
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
        import geojson
    except:
        raise Exception("\"geojson\" is not installed; run \"pip install --user geojson\"") from None
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
                "image.interpolation" : "none",                                 # NOTE: See https://matplotlib.org/stable/gallery/images_contours_and_fields/interpolation_methods.html
                     "image.resample" : False,
            }
        )
        import matplotlib.pyplot
    except:
        raise Exception("\"matplotlib\" is not installed; run \"pip install --user matplotlib\"") from None
    try:
        import shapely
        import shapely.geometry
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
            description = "Demonstrate a potential new method.",
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
        "--GSHHG-resolution",
        choices = [
            "c",                        # crude
            "l",                        # low
            "i",                        # intermediate
            "h",                        # high
            "f",                        # full
        ],
        default = "c",                  # crude
           dest = "gshhgRes",
           help = "the resolution of the GSHHG dataset",
           type = str,
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
        "--simplification-factor",
        default = 0.0001,
           dest = "simpFact",
           help = "the multiplication factor to simplify shapes by, relative to the buffering distance",
           type = float,
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
    onlyValid = True
    repair = True

    # Create short-hands and make output folder if it is missing ...
    dName1 = f"newOutput/gshhgRes={args.gshhgRes}"
    dName2 = f"{dName1}/eps={args.eps:.2e}_fillFact=×{args.fillFact:.2e}_nAng={args.nAng:d}_nIter={args.nIter:d}_simpFact=×{args.simpFact:.2e}_tol={args.tol:.2e}°"
    if not os.path.exists(dName2):
        os.makedirs(dName2)

    # **************************************************************************

    # Initialize list ...
    polys = []

    # Loop over records in the GSHHG Shapefile for the boundary between land and
    # ocean at the user-requested resolution ...
    for record in cartopy.io.shapereader.Reader(
        cartopy.io.shapereader.gshhs(
            level = 1,
            scale = args.gshhgRes,
        )
    ).records():
        # Skip bad records ...
        if not hasattr(record, "geometry"):
            continue

        # Append Polgons to list ...
        polys += pyguymer3.geo.extract_polys(
            record.geometry,
            onlyValid = onlyValid,
               repair = repair,
        )

    # Convert list of Polygons to a MultiPolygon ...
    multiPolys = shapely.geometry.multipolygon.MultiPolygon(polys)

    # Save MultiPolygon ...
    if not os.path.exists(f"{dName1}/coastline.wkb.gz"):
        with gzip.open(f"{dName1}/coastline.wkb.gz", mode = "wb", compresslevel = 9) as gzObj:
            gzObj.write(shapely.wkb.dumps(multiPolys))

    # Save MultiPolygon ...
    if not os.path.exists(f"{dName1}/coastline.geojson"):
        with open(f"{dName1}/coastline.geojson", "wt", encoding = "utf-8") as fObj:
            geojson.dump(
                multiPolys,
                fObj,
                ensure_ascii = False,
                      indent = 4,
                   sort_keys = True,
            )

    # Clean up ...
    del multiPolys

    # **************************************************************************

    # Loop over buffering steps ...
    for distStep in [
        250,
         50,
         10,
          2,
    ]:
        # Create short-hands ...
        fill = args.fillFact * float(1000 * distStep)                           # [m]
        simp = args.simpFact * float(1000 * distStep) / pyguymer3.RESOLUTION_OF_EARTH   # [°]

        # Set the list of Polygons to be the un-buffered list of Polygons ...
        buffPolys = copy.copy(polys)

        # Loop over buffering distances ...
        for dist in range(distStep, 250 + distStep, distStep):
            # Skip short buffering steps if they are a long away from the known
            # solution ...
            if distStep == 50:
                if dist <   0 or dist > 250:
                    continue
            if distStep == 10:
                if dist < 200 or dist > 250:
                    continue
            if distStep == 2:
                if dist < 220 or dist > 230:
                    continue

            # Create short-hands and skip calculating this distance if the
            # output files already exist and just load them ...
            # NOTE: Given how the Polygons were made, we know that there aren't
            #       any invalid Polygons, so don't bother checking for them.
            gName = f"{dName2}/dist={dist:03d}km.geojson"
            wName = f"{dName2}/dist={dist:03d}km.wkb.gz"
            if os.path.exists(gName) and os.path.exists(wName):
                print(f"Loading \"{wName}\" ...")
                with gzip.open(wName, mode = "rb") as gzObj:
                    buffPolys = pyguymer3.geo.extract_polys(
                        shapely.wkb.loads(gzObj.read()),
                        onlyValid = False,
                           repair = False,
                    )
                continue

            print(f"Making \"{wName}\" (and GeoJSON too) ...")

            # ******************************************************************

            # Initialize list ...
            holes = []

            # Create short-hands ...
            nPolys = len(buffPolys)                                             # [#]
            start = pyguymer3.now()

            # Loop over Polygons ...
            for iPoly, poly in enumerate(buffPolys):
                # Print progress ...
                # NOTE: The progress string needs padding with extra spaces so
                #       that the line is fully overwritten when it inevitably
                #       gets shorter (as the remaining time gets shorter).
                #       Assume that the longest it will ever be is
                #       "???.???% (~??h ??m ??.?s still to go)" (which is 37
                #       characters).
                fraction = float(iPoly + 1) / float(nPolys)
                durationSoFar = pyguymer3.now() - start
                totalDuration = durationSoFar / fraction
                remaining = (totalDuration - durationSoFar).total_seconds()     # [s]
                progress = f"{100.0 * fraction:.3f}% (~{pyguymer3.convert_seconds_to_pretty_time(remaining)} still to go)"
                print(f"  Buffering Polygons ... {progress:37s}", end = "\r")

                # Loop over the Polygons in the buffer of the Polygon ...
                # NOTE: Given how the buffer is made, we know that there aren't
                #       any invalid Polygons, so don't bother checking for them.
                for buffPoly in pyguymer3.geo.extract_polys(
                    pyguymer3.geo.buffer(
                        poly.exterior,
                        float(1000 * distStep),
                                debug = args.debug,
                                  eps = args.eps,
                                 fill = fill,
                            fillSpace = "GeodesicSpace",
                        keepInteriors = True,
                                 nAng = args.nAng,
                                nIter = args.nIter,
                             ramLimit = args.ramLimit,
                                 simp = simp,
                                  tol = args.tol,
                    ),
                    onlyValid = False,
                       repair = False,
                ):
                    # Loop over interior rings ...
                    for interior in buffPoly.interiors:
                        # Convert LinearRing to Polygon and skip this hole if it
                        # is outside the original Polygon ...
                        hole = shapely.geometry.polygon.Polygon(interior)
                        if hole.disjoint(poly):
                            continue

                        # Append Polygon to list ...
                        holes.append(hole)

            # Clear the line ...
            print()

            # Convert list of Polygons to a MultiPolygon ...
            multiHoles = shapely.geometry.multipolygon.MultiPolygon(holes)

            # Save MultiPolygon ...
            with gzip.open(wName, mode = "wb", compresslevel = 9) as gzObj:
                gzObj.write(shapely.wkb.dumps(multiHoles))

            # Save MultiPolygon ...
            with open(gName, "wt", encoding = "utf-8") as fObj:
                geojson.dump(
                    multiHoles,
                    fObj,
                    ensure_ascii = False,
                          indent = 4,
                       sort_keys = True,
                )

            # Clean up ...
            del multiHoles

            # ******************************************************************

            # Replace the old list of Polygons with the new list of Polygons and
            # clean up ...
            buffPolys = copy.copy(holes)
            del holes
