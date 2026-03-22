#!/usr/bin/env bash

# Check that non-standard programs are installed. "standard" programs are
# anything that is specified in the POSIX.1-2008 standard (and the IEEE Std
# 1003.1 standard) or that is a BASH builtin command. Therefore, "non-standard"
# programs are anything that does not appear on the following two lists:
#   * https://pubs.opengroup.org/onlinepubs/9699919799/idx/utilities.html
#   * https://www.gnu.org/software/bash/manual/html_node/Bash-Builtins.html
if ! type python3.12 &> /dev/null; then
    echo "ERROR: \"python3.12\" is not installed." >&2
    exit 1
fi

# Create short-hands ...
fillFactor=0.02
nAng=181
ramLimit=4294967296
simpFactor=0.0004
timeout=600.0

# Run Python script ...
python3.12 newMethodScope.py                                                    \
    --fill-factor "${fillFactor}"                                               \
    --nAng "${nAng}"                                                            \
    --RAM-limit ${ramLimit}

# Loop over GSHHG resolutions ...
for gshhgRes in "c" "l" "i" "h" "f"; do
    # Run Python script ...
    python3.12 newMethod.py                                                     \
        --fill-factor "${fillFactor}"                                           \
        --GSHHG-resolution "${gshhgRes}"                                        \
        --nAng "${nAng}"                                                        \
        --RAM-limit "${ramLimit}"                                               \
        --simplification-factor "${simpFactor}"
done

# Run Python script ...
python3.12 plotNewMethod.py                                                     \
    --fill-factor "${fillFactor}"                                               \
    --nAng "${nAng}"                                                            \
    --RAM-limit "${ramLimit}"                                                   \
    --simplification-factor "${simpFactor}"                                     \
    --timeout "${timeout}"
