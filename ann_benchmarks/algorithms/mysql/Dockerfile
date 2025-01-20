FROM ann-benchmarks

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get upgrade -y && apt-get install -y \
      build-essential \
      bison \
      cmake \
      fakeroot \
      gdb \
      git-core \
      libaio-dev \
      libjson-perl \
      libnuma-dev \
      libtinfo-dev \
      libtirpc-dev \
      libssl-dev \
      lsb-release \
      perl \
      pkg-config \
      python3-mysql.connector \
      tzdata \
      unzip \
      valgrind \
      zip \
      zlib1g-dev

RUN if [ "$(lsb_release -cs)" = "jammy" ]; then \
        apt-get install -y gcc-12 g++-12; \
        update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-12 10; \
        update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-12 10; \
    fi

RUN adduser --disabled-password --no-create-home --gecos '' bob --uid 1234

ADD --chown=1234 ann_benchmarks/algorithms/mysql/mysql-src/ /src
WORKDIR /src

USER bob
RUN mkdir build
WORKDIR /src/build
RUN cmake \
  -DWITH_BOOST=boost-lib \
  -DDOWNLOAD_BOOST=1 \
  -DBUILD_CONFIG=mysql_release \
  -DCMAKE_INSTALL_PREFIX=/usr \
  -DCMAKE_BUILD_TYPE=Release \
  -DSYSCONFDIR=/etc/mysql \
  -DMYSQL_UNIX_ADDR=/var/run/mysqld/mysqld.sock \
  -DWITH_MECAB= \
  -DWITH_NUMA=OFF \
  -DCOMPILATION_COMMENT="PlanetScale MySQL" \
  -DCOMPILATION_COMMENT_SERVER="PlanetScale MySQL Server" \
  -DINSTALL_LAYOUT=DEB \
  -DREPRODUCIBLE_BUILD=OFF \
\
  -DENABLED_PROFILING=OFF \
  -DENABLE_GCOV=OFF \
  -DENABLE_GPROF=OFF \
  -DWITH_CLIENT_PROTOCOL_TRACING=OFF \
  -DWITH_DEBUG=OFF \
  -DWITH_INNODB_EXTRA_DEBUG=OFF \
  -DWITH_KERBEROS=none \
  -DWITH_AUTHENTICATION_CLIENT_PLUGINS=OFF \
  -DWITH_AUTHENTICATION_FIDO=OFF \
  -DWITH_AUTHENTICATION_KERBEROS=OFF \
  -DWITH_AUTHENTICATION_LDAP_DEFAULT=OFF \
  -DWITH_COMPONENT_KEYRING_FILE=OFF \
  -DINSTALL_MYSQLTESTDIR=\
  -DINSTALL_STATIC_LIBRARIES=OFF \
  -DWITH_ROUTER=OFF \
  -DWITH_UNIT_TESTS=OFF \
  ..

RUN make -j8

USER root
RUN mkdir -p /var/lib/mysql /var/run/mysqld /var/lib/mysql-files
RUN chown 1234 -R /var/lib/mysql /var/run/mysqld /var/lib/mysql-files

USER bob
RUN /src/build/runtime_output_directory/mysqld --initialize-insecure

WORKDIR /home/app
USER root

# Custom entrypoint that also starts the MySQL server.
RUN echo 'set -eux' >> entrypoint.sh
RUN echo 'su bob -c "nohup /src/build/runtime_output_directory/mysqld --with-ps-vectors > /tmp/nohup.out 2>&1 & sleep 5"' >> entrypoint.sh
RUN echo 'python3 -u run_algorithm.py "$@"' >> entrypoint.sh

ENTRYPOINT ["/bin/bash", "/home/app/entrypoint.sh"]
