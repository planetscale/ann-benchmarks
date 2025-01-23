# Adopted from https://github.com/microsoft/SPTAG/blob/master/Dockerfile

FROM ann-benchmarks
RUN apt-get update && apt-get -y install wget build-essential cmake libboost-all-dev libtbb-dev software-properties-common swig
# SPTAG defaults to Python 2 if it's found on the system, so as a hack, we remove it. See https://github.com/microsoft/SPTAG/blob/master/Wrappers/CMakeLists.txt
RUN apt-get -y remove libpython2.7

RUN apt-get -y install ninja-build

ADD --chown=1234 ann_benchmarks/algorithms/sptag/SPTAG/ ./SPTAG
# Compile
RUN cd SPTAG && mkdir build && cd build && cmake -GNinja .. && ninja && cd ..

# so python can find the SPTAG module
ENV PYTHONPATH=/home/app/SPTAG/Release
RUN python3 -c 'import SPTAG'
