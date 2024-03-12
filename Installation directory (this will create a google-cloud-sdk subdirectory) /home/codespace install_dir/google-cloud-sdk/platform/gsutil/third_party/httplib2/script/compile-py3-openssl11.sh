#!not for running standalone, see .github/workflows/test.yaml

cache_dir=$HOME/.cache
install_dir=$cache_dir/py3-openssl11
python_version="3.7.3"
openssl_version="1.1.1f"
cpucount=$(nproc --all)
export PYTHONDONTWRITEBYTECODE=1

#rm -rf $cache_dir/* # uncomment to rebuild

if [[ ! -x "$install_dir/bin/python" ]] || [[ $($install_dir/bin/python -V) != "Python $python_version" ]] ; then
  (
  mkdir -p /tmp/source
  cd /tmp/source
  # Compile OpenSSL
  curl -fLOsS "https://www.openssl.org/source/openssl-$openssl_version.tar.gz"
  echo "Extracting OpenSSL..."
  tar xf openssl-$openssl_version.tar.gz
  cd ./openssl-$openssl_version
  echo "Compiling OpenSSL $openssl_version..."
  ./config shared --prefix=$install_dir
  echo "Running make for OpenSSL..."
  make -j$cpucount -s
  echo "Running make install for OpenSSL..."
  make install_sw >/dev/null
  export LD_LIBRARY_PATH=$install_dir/lib

  cd /tmp/source
  sudo apt install -qq --yes libffi-dev
  # Compile latest Python
  curl -fLOsS "https://www.python.org/ftp/python/$python_version/Python-$python_version.tar.xz"
  echo "Extracting Python..."
  tar xf Python-$python_version.tar.xz
  cd ./Python-$python_version
  echo "Compiling Python $python_version..."
  # Note we are purposefully NOT using optimization flags as they increase compile time 10x
  conf_flags="--with-openssl=$install_dir --prefix=$install_dir --with-ensurepip=upgrade"
  CFLAGS=-O1 ./configure $conf_flags > /dev/null
  make -j$cpucount -s
  echo "Installing Python..."
  make altinstall bininstall >/dev/null
  ln -fs pip3.7 $install_dir/bin/pip3
  ln -fs pip3 $install_dir/bin/pip
  ln -fs python3 $install_dir/bin/python
  # care for CI cache size
  find $install_dir -type d -name __pycache__ -print0 |xargs -0 rm -rf
  )
fi

export LD_LIBRARY_PATH=$install_dir/lib
export PATH=$install_dir/bin:$PATH
if [[ $(python -V) != "Python $python_version" ]] ; then
  echo "Required Python version was not installed into PATH" >&2
  exit 1
fi
if [[ $(python -c 'import ssl; print(ssl.OPENSSL_VERSION)') != OpenSSL\ ${openssl_version}* ]] ; then
  echo "Required OpenSSL version was not installed into Python" >&2
  exit 1
fi
