# Saas - Screenshot as a service [![](https://circleci.com/gh/nattvara/saas.svg?style=shield)](https://circleci.com/gh/nattvara/saas)

[![saas demo](https://asciinema.org/a/KwtTFXEi4EhdsDUTglcw7aH8q.svg)](https://asciinema.org/a/KwtTFXEi4EhdsDUTglcw7aH8q?autoplay=1)


## Installation

### Requirements

#### FUSE

__What is fuse?__ From the [FUSE wikipedia page](https://en.wikipedia.org/wiki/Filesystem_in_Userspace)

> Filesystem in Userspace (FUSE) is a software interface for Unix-like computer operating systems that lets non-privileged users create their own file systems without editing kernel code. This is achieved by running file system code in user space while the FUSE module provides only a "bridge" to the actual kernel interfaces.

FUSE is used to mount a synthetic filesystem to read back the photos taken of the url given to saas. The user-space filesystem is dynamically filled with files and directories by saas. FUSE makes a good choice for this component since this can be easily integrated into almost any workflow, read more about this in the [API section](#api).

#### Elasticsearch

[Elasticsearch](https://www.elastic.co/products/elasticsearch) is used as a storage backend for saas. Read more about the storage in the [storage section](#storage).

#### ImageMagick

[ImageMagick](https://www.imagemagick.org) is used for optimizing image files saved to disk. This is an optional dependency since it is only used when the `--optimize-storage` flag is used.

### Linux

__1. Install Elasticsearch__ [using docker](https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html)

```bash
sudo docker pull docker.elastic.co/elasticsearch/elasticsearch:6.5.4
```

__2. Install Firefox and Geckodriver__

```bash
sudo apt-get install firefox

wget https://github.com/mozilla/geckodriver/releases/download/v0.23.0/geckodriver-v0.23.0-linux64.tar.gz
tar -xvzf geckodriver-v0.23.0-linux64.tar.gz
chmod +x geckodriver
sudo mv geckodriver /usr/bin/
```

__3. Install ImageMagick (optional)__

```bash
sudo apt-get install imagemagick
```

__4. Install saas__

```bash
# Make sure you have Python 3.7 installed!
python --version
# Python 3.7.2

pip install saas

saas --version
# saas 1.1.3.1
```

### macOS

__1. Install FUSE for macOS__

Either from [official website (recommended)](https://osxfuse.github.io/) or using homebrew

```bash
brew update
brew tap homebrew/cask
brew cask install osxfuse
```

__2. Install Elasticsearch__

```bash
brew install elasticsearch
```

__3. Install Firefox and Geckodriver__

Either from [official website](https://mozilla.org/firefox) or using homebrew

```bash
brew cask install firefox
```

__4. Install Geckodriver__

```bash
brew install geckodriver
```

__5. Install Python 3.7__

```bash
brew install python3
python3 --version
# Python 3.7.2
```

__6. Install ImageMagick (optional)__

```bash
brew install imagemagick
```

__7. Install saas__

```bash
# Make sure you have Python 3.7 installed!
python3 --version
# Python 3.7.2

python3 -m pip install saas

saas --version
# saas 1.1.3.1
```

## Usage

### Getting started

#### Start Elasticsearch

Everytime you run saas you must make sure that there is an elasticsearch instance running and availible is availible for saas to connect to.

##### If using docker

```bash
sudo docker run -d -p 9200:9200 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:6.5.4
```

##### If binary exists in PATH

```bash
# foreground
elasticsearch

# or run it in the background
elasticsearch 2>&1 > elasticsearch.log &
```

#### Taking a picture of a single URL

```console

# create input file
$ touch input_urls

# make mountpoint for filesystem
$ mkdir mount

# start saas
# the --ignore-found-urls option will disable the crawler behaviour
$ saas input_urls mount --ignore-found-urls
mounting filesystem at: ./mount
starting 1 crawler threads
starting 1 photographer threads

# add url to input file
$ echo "https://news.ycombinator.com/" >> input_urls

# the photo will appear inside the mountpoint
$ tree mount/
mount/
└── news.ycombinator.com
    ├── 2019011721
    │   └── index.png
    └── latest
        └── index.png

3 directories, 2 files
```

### Using the crawler

The crawler is a useful tool to find new urls to take pictuers of. It can be configured to *run wild* and crawl any domain it comes across, or stay at the domains that the urls in the input file belongs to.

#### Stay at domains

Using the `--stay-at-domain` flag the crawler will discard any domain that does not belong to the same domain as the page it was found at.

```console

$ saas input_urls mount --stay-at-domain

$ echo "https://daringfireball.net/" >> input_urls

# after a minute or so

$ tree mount/daringfireball.net/latest/
mount/daringfireball.net/latest/
├── 2006
│   └── 06
│       └── apple_open_source.png
├── 2007
│   └── 01
│       └── enderle_leg_pulling.png
├── 2008
│   └── 04
│       └── big_fan.png.rendering.saas
├── 2017
│   └── 07
│       └── you_should_not_force_quit_apps.png
├── 2019
│   └── 01
│       └── on_getting_started_with_regular_expressions.png
├── index.png
└── linked
    └── 2019
        └── 01
            └── 07
                └── samsung-itunes.png

14 directories, 7 files
```

### Resetting the data

Since the mounted filesystem is a read-only filesystem simply removing the a photo from the filesystem is currently not possible.

For now, at least, the best way to clear the data directory and the index is by using the `--clear-data-dir` and `--clear-elasticsearch` options

```console
# cannot modify the mounted filesystem
$ touch mount/foo
touch: mount/foo: Read-only file system

# clear the index of urls and photo metadata
$ saas input_urls mount --clear-elasticsearch

# clear the photo files
$ saas input_urls mount --clear-data-dir
```

[Read more about storage](#storage)

### Setting the viewport size

The camera viewport can be adjusted with the `--viewport-width` and `--viewport-height` options.

By default the camera tries to take a full screen screenshot. This means that it figures out how tall a page is and resizes the camera height accordingly. Full screen screenshots take way longer time, especially on image-heavy sites.

### Full list of options

```
usage: saas [-h] [--version] [--debug] [--refresh-rate] [--crawler-threads]
            [--photographer-threads] [--data-dir] [--clear-data-dir]
            [--elasticsearch-host] [--setup-elasticsearch]
            [--clear-elasticsearch] [--stay-at-domain] [--ignore-found-urls]
            [--viewport-width] [--viewport-height] [--viewport-max-height]
            [--optimize-storage] [--stop-if-idle]
            url_file mountpoint

Screenshot as a service

positional arguments:
  url_file              Path to input url file
  mountpoint            Where to mount filesystem via FUSE

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --debug               Display debugging information
  --refresh-rate        Refresh captures of urls every 'day', 'hour' or
                        'minute' (default: hour)
  --crawler-threads     Number of crawler threads, usually not neccessary with
                        more than one (default: 1)
  --photographer-threads
                        Number of photographer threads, beaware that
                        increasing too much won't neccessarily speed up
                        performance and hog the system (default: 1)
  --data-dir            Path to data directory (default: ~/.saas-data-dir)
  --clear-data-dir      Use flag to clear data directory on start
  --elasticsearch-host
                        Elasticsearch host (default: localhost:9200)
  --setup-elasticsearch
                        Use flag to create indices in elasticsearch
  --clear-elasticsearch
                        Use flag to clear elasticsearch on start, WARNING:
                        this will clear all indices found in elasticsearch
                        instance
  --stay-at-domain      Use flag to ignore urls from a different domain than
                        the one it was found at
  --ignore-found-urls   Use flag to ignore urls found on crawled urls
  --viewport-width      Width of camera viewport in pixels (default: 1920)
  --viewport-height     Height of camera viewport in pixels, if set to 0
                        camera will try to take a full height high quality
                        screenshot, which is way slower than fixed size
                        (default: 0)
  --viewport-max-height
                        Max height of camera viewport in pixels, if
                        --viewport-height is set this will be ignored
  --optimize-storage    Image files should be optimized to take up less
                        storage (takes longer time to render)
  --stop-if-idle        If greater than 0 saas will stop if it is idle for
                        more than the provided number of minutes
```

<p id="storage"></p>

## Storage

Saas uses two types of storages. A regular directory for storage of photo files, and elasticsearch for photo metadata and urls.

### Elasticsearch

The elastic search instance is configured by saas with three indices

 - `crawled` this index holds urls that crawler have visited, the HTTP response code and any locks (meaning any photographer thread is taking a picture of that url)
 - `uncrawled` this index contains scraped urls from pages crawler have visited
 - `photos` this index contains photo metadata, file size, captured_at, filename etc.

### Data directory

When saas responds to a directory listing it only needs to query the elasticsearch `photos` index. Only when a read request is made, the actual file content is fetched from the data directory. The data directory holds the raw photo data with a unique id for each photo. Default path for this directory is `~/.saas-data-dir`

```console
$ tree ~/.saas-data-dir/
├── 18
│   └── 18dfe716-cdb2-4916-8154-6088d9bc6ee3.png
├── 1c
│   └── 1c1d0ee8-28f6-4b7c-b70f-8e800c58a3a6.png
├── 29
│   └── 29dd23f3-1791-46e6-8a83-25f5736a0894.png
├── 50
│   └── 50f13985-2cce-4464-942d-d9bbea165785.png
├── 76
│   └── 769933ce-2cde-4f30-a215-c26227850c8b.png
├── 89
│   ├── 8975f15c-7112-499c-97d5-44dd501b9b09.png
│   └── 89ec9675-84f8-47fa-9589-8d39a8a34ea1.png
├── ab
│   └── ab5bbb0f-03cb-45ed-be1d-e257434a925c.png
├── ca
│   └── ca1551a2-8855-4d0d-869b-108b9b7122bf.png
└── d7
    └── d79598a2-619f-4192-bb39-5e31642be800.png
```

## Build

Install saas by cloning it from source

```console
$ git clone https://github.com/nattvara/saas.git && cd saas

$ python3 -m venv ./venv

$ source ./venv/bin/activate

$ python setup.py develop
```

### Firefox extensions

The camera module uses selenium to render pages. To improve performance saas uses [uBlock Origin](https://github.com/gorhill/uBlock) to block ads. To have greater access to more webpages saas uses [I don't care about cookies](https://www.i-dont-care-about-cookies.eu/) to bypass popups and GDPR consent forms. Many websites also employ the practice of paywalls for some of their content, however, many websites leave their site open to users coming from search engines and social media sites. Saas therefore has a small custom [firefox extension](extensions/referer_header) to rewrite all http requests made from firefox to include the header `Referer: https://google.com` - this will allow access to a lot more content on the web.

#### Updating uBlock Origin

Download the latest ublock.xpi from [gorhill/uBlock releases](https://github.com/gorhill/uBlock/releases) and replace the version in the `extensions/` directory.

#### Updating IDCAC

Download and install the latest version using firefox from [https://www.i-dont-care-about-cookies.eu/](https://www.i-dont-care-about-cookies.eu/). Locate the `.xpi` file inside Firefox's extensions directory, on macOS this is `~/Library/Application Support/Firefox/Profiles/[profile]/extensions/`. Copy the `.xpi` file to the `extensions/` directory.

#### Referer Header

Make zip archive of source files

```bash
zip -r -j -FS extensions/referer_header.xpi extensions/referer_header/*
```

### Run the testsuite

```console
$ python -m unittest discover -s tests
```

### Run the typechecker

```console
$ mypy saas
```

<p id="api"></p>

## API

The main reason for using FUSE is that saas's api _is the filesystem_. Everything that can interact with the filesystem can interact with saas. Almost every programming language ships with easy access to the filesystem, hence integration in any environment is as easy as reading and writing to the filesystem.

For example exposing saas through a http interface could be as easy as starting a super simple node service like the following (should definitely be more thorough than this in production).

```js
const http = require('http')
const url = require('url')
const fs = require('fs');
const port = 3000

const requestHandler = (request, response) => {
    fs.appendFile(
        'urls',
        url.parse(request.url, true).query.url + '\n',
        () => {}
    )
    response.end('')
}

const server = http.createServer(requestHandler)
server.listen(port, (err) => {})
```

This would allow for adding new urls to crawl by calling the service like the following

```bash
curl http://localhost:3000/?url=https%3A%2F%2Fwww.wsj.com%2F
curl http://localhost:3000/?url=https%3A%2F%2Fwww.nytimes.com%2F
```

Starting a simple python webserver could allow for traversing the saas filesystem

```bash
# inside mounted filesystem
python -m SimpleHTTPServer 3001

# so the following url
# https://www.ft.com/content/180f3428-1923-11e9-b93e-f4351a53f1c3
# if photographed, could be found at
wget http://localhost:3001/www.ft.com/latest/content/180f3428-1923-11e9-b93e-f4351a53f1c3.png
```

Those are two out of a hundred ways to integrate/extend saas.

## Performance and Scalability

Saas is designed to run over multiple machines. There can be virtually unlimited number of saas-nodes added to a single cluster, the only two things they need is a common elasticsearch instance or cluster to talk to, and a common data directory. Elasticsearch is well known for its scalability and the data directory could for instance be a network drive they share, Amazon EFS or any other way to share a drive between machines.

Since all nodes in a cluster share the same index and data directory they can all read the images the cluster as a whole produces. Nodes can also join and leave the cluster freely without incurring any long time data loss.

The biggest hit to performance are taking photos of image-heavy sites or using a large viewport size. Fixed viewport size is a good option for optimizing performance, there is virtually no upper limit to how large a website can be vertically. Screenshots of tabloid websites or sites with infinite-scroll can easily reach 25-50 MB in size.

Checkout the guide [Maximize saas throughput](docs/maximize_throughput_guide.md) for a thorough guide for how to deploy a large cluster of saas nodes on AWS and optimize performance.

## Examples

See [examples/](examples/README.md) for some good examples for testing saas.

## Known issues

Under some circumstances, a fatal crash for instance, the mounted filesystem might not unmount automatically. Also the filesystem will not be able to unmount if some other process is currently reading from the filesystem.

If you encouter this, run

```bash
umount path/to/mounted_directory
```

## License

MIT © Ludwig Kristoffersson

See [LICENSE file](LICENSE) for more information
