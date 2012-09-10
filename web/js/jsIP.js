var require = function (file, cwd) {
    var resolved = require.resolve(file, cwd || '/');
    var mod = require.modules[resolved];
    if (!mod) throw new Error(
        'Failed to resolve module ' + file + ', tried ' + resolved
    );
    var res = mod._cached ? mod._cached : mod();
    return res;
}

require.paths = [];
require.modules = {};
require.extensions = [".js",".coffee"];

require._core = {
    'assert': true,
    'events': true,
    'fs': true,
    'path': true,
    'vm': true
};

require.resolve = (function () {
    return function (x, cwd) {
        if (!cwd) cwd = '/';
        
        if (require._core[x]) return x;
        var path = require.modules.path();
        cwd = path.resolve('/', cwd);
        var y = cwd || '/';
        
        if (x.match(/^(?:\.\.?\/|\/)/)) {
            var m = loadAsFileSync(path.resolve(y, x))
                || loadAsDirectorySync(path.resolve(y, x));
            if (m) return m;
        }
        
        var n = loadNodeModulesSync(x, y);
        if (n) return n;
        
        throw new Error("Cannot find module '" + x + "'");
        
        function loadAsFileSync (x) {
            if (require.modules[x]) {
                return x;
            }
            
            for (var i = 0; i < require.extensions.length; i++) {
                var ext = require.extensions[i];
                if (require.modules[x + ext]) return x + ext;
            }
        }
        
        function loadAsDirectorySync (x) {
            x = x.replace(/\/+$/, '');
            var pkgfile = x + '/package.json';
            if (require.modules[pkgfile]) {
                var pkg = require.modules[pkgfile]();
                var b = pkg.browserify;
                if (typeof b === 'object' && b.main) {
                    var m = loadAsFileSync(path.resolve(x, b.main));
                    if (m) return m;
                }
                else if (typeof b === 'string') {
                    var m = loadAsFileSync(path.resolve(x, b));
                    if (m) return m;
                }
                else if (pkg.main) {
                    var m = loadAsFileSync(path.resolve(x, pkg.main));
                    if (m) return m;
                }
            }
            
            return loadAsFileSync(x + '/index');
        }
        
        function loadNodeModulesSync (x, start) {
            var dirs = nodeModulesPathsSync(start);
            for (var i = 0; i < dirs.length; i++) {
                var dir = dirs[i];
                var m = loadAsFileSync(dir + '/' + x);
                if (m) return m;
                var n = loadAsDirectorySync(dir + '/' + x);
                if (n) return n;
            }
            
            var m = loadAsFileSync(x);
            if (m) return m;
        }
        
        function nodeModulesPathsSync (start) {
            var parts;
            if (start === '/') parts = [ '' ];
            else parts = path.normalize(start).split('/');
            
            var dirs = [];
            for (var i = parts.length - 1; i >= 0; i--) {
                if (parts[i] === 'node_modules') continue;
                var dir = parts.slice(0, i + 1).join('/') + '/node_modules';
                dirs.push(dir);
            }
            
            return dirs;
        }
    };
})();

require.alias = function (from, to) {
    var path = require.modules.path();
    var res = null;
    try {
        res = require.resolve(from + '/package.json', '/');
    }
    catch (err) {
        res = require.resolve(from, '/');
    }
    var basedir = path.dirname(res);
    
    var keys = (Object.keys || function (obj) {
        var res = [];
        for (var key in obj) res.push(key)
        return res;
    })(require.modules);
    
    for (var i = 0; i < keys.length; i++) {
        var key = keys[i];
        if (key.slice(0, basedir.length + 1) === basedir + '/') {
            var f = key.slice(basedir.length);
            require.modules[to + f] = require.modules[basedir + f];
        }
        else if (key === basedir) {
            require.modules[to] = require.modules[basedir];
        }
    }
};

require.define = function (filename, fn) {
    var dirname = require._core[filename]
        ? ''
        : require.modules.path().dirname(filename)
    ;
    
    var require_ = function (file) {
        return require(file, dirname)
    };
    require_.resolve = function (name) {
        return require.resolve(name, dirname);
    };
    require_.modules = require.modules;
    require_.define = require.define;
    var module_ = { exports : {} };
    
    require.modules[filename] = function () {
        require.modules[filename]._cached = module_.exports;
        fn.call(
            module_.exports,
            require_,
            module_,
            module_.exports,
            dirname,
            filename
        );
        require.modules[filename]._cached = module_.exports;
        return module_.exports;
    };
};

if (typeof process === 'undefined') process = {};

if (!process.nextTick) process.nextTick = (function () {
    var queue = [];
    var canPost = typeof window !== 'undefined'
        && window.postMessage && window.addEventListener
    ;
    
    if (canPost) {
        window.addEventListener('message', function (ev) {
            if (ev.source === window && ev.data === 'browserify-tick') {
                ev.stopPropagation();
                if (queue.length > 0) {
                    var fn = queue.shift();
                    fn();
                }
            }
        }, true);
    }
    
    return function (fn) {
        if (canPost) {
            queue.push(fn);
            window.postMessage('browserify-tick', '*');
        }
        else setTimeout(fn, 0);
    };
})();

if (!process.title) process.title = 'browser';

if (!process.binding) process.binding = function (name) {
    if (name === 'evals') return require('vm')
    else throw new Error('No such module')
};

if (!process.cwd) process.cwd = function () { return '.' };

if (!process.env) process.env = {};
if (!process.argv) process.argv = [];

require.define("path", function (require, module, exports, __dirname, __filename) {
function filter (xs, fn) {
    var res = [];
    for (var i = 0; i < xs.length; i++) {
        if (fn(xs[i], i, xs)) res.push(xs[i]);
    }
    return res;
}

// resolves . and .. elements in a path array with directory names there
// must be no slashes, empty elements, or device names (c:\) in the array
// (so also no leading and trailing slashes - it does not distinguish
// relative and absolute paths)
function normalizeArray(parts, allowAboveRoot) {
  // if the path tries to go above the root, `up` ends up > 0
  var up = 0;
  for (var i = parts.length; i >= 0; i--) {
    var last = parts[i];
    if (last == '.') {
      parts.splice(i, 1);
    } else if (last === '..') {
      parts.splice(i, 1);
      up++;
    } else if (up) {
      parts.splice(i, 1);
      up--;
    }
  }

  // if the path is allowed to go above the root, restore leading ..s
  if (allowAboveRoot) {
    for (; up--; up) {
      parts.unshift('..');
    }
  }

  return parts;
}

// Regex to split a filename into [*, dir, basename, ext]
// posix version
var splitPathRe = /^(.+\/(?!$)|\/)?((?:.+?)?(\.[^.]*)?)$/;

// path.resolve([from ...], to)
// posix version
exports.resolve = function() {
var resolvedPath = '',
    resolvedAbsolute = false;

for (var i = arguments.length; i >= -1 && !resolvedAbsolute; i--) {
  var path = (i >= 0)
      ? arguments[i]
      : process.cwd();

  // Skip empty and invalid entries
  if (typeof path !== 'string' || !path) {
    continue;
  }

  resolvedPath = path + '/' + resolvedPath;
  resolvedAbsolute = path.charAt(0) === '/';
}

// At this point the path should be resolved to a full absolute path, but
// handle relative paths to be safe (might happen when process.cwd() fails)

// Normalize the path
resolvedPath = normalizeArray(filter(resolvedPath.split('/'), function(p) {
    return !!p;
  }), !resolvedAbsolute).join('/');

  return ((resolvedAbsolute ? '/' : '') + resolvedPath) || '.';
};

// path.normalize(path)
// posix version
exports.normalize = function(path) {
var isAbsolute = path.charAt(0) === '/',
    trailingSlash = path.slice(-1) === '/';

// Normalize the path
path = normalizeArray(filter(path.split('/'), function(p) {
    return !!p;
  }), !isAbsolute).join('/');

  if (!path && !isAbsolute) {
    path = '.';
  }
  if (path && trailingSlash) {
    path += '/';
  }
  
  return (isAbsolute ? '/' : '') + path;
};


// posix version
exports.join = function() {
  var paths = Array.prototype.slice.call(arguments, 0);
  return exports.normalize(filter(paths, function(p, index) {
    return p && typeof p === 'string';
  }).join('/'));
};


exports.dirname = function(path) {
  var dir = splitPathRe.exec(path)[1] || '';
  var isWindows = false;
  if (!dir) {
    // No dirname
    return '.';
  } else if (dir.length === 1 ||
      (isWindows && dir.length <= 3 && dir.charAt(1) === ':')) {
    // It is just a slash or a drive letter with a slash
    return dir;
  } else {
    // It is a full dirname, strip trailing slash
    return dir.substring(0, dir.length - 1);
  }
};


exports.basename = function(path, ext) {
  var f = splitPathRe.exec(path)[2] || '';
  // TODO: make this comparison case-insensitive on windows?
  if (ext && f.substr(-1 * ext.length) === ext) {
    f = f.substr(0, f.length - ext.length);
  }
  return f;
};


exports.extname = function(path) {
  return splitPathRe.exec(path)[3] || '';
};

});

require.define("/jsIP.js", function (require, module, exports, __dirname, __filename) {
    var compactIPv4 = function (bytes) {
	return [(bytes[0]<<8) + bytes[1], (bytes[2]<<8) + bytes[3]];
}

var parseIPv4 = function (addr_str) {
	bytes = addr_str.split('.');
	if (bytes.length > 4) throw "IPv4 address too long";
	filler = [];
	for (i=0; i<8; i++) { filler.push(0); }
	bytes = new Array().concat(filler.slice(0, (4 - bytes.length)), bytes);
	for (i in bytes) {
		bytes[i] = parseInt(bytes[i]);
		if (bytes[i] > 255) throw 'IPv4 Error: section too large';
	}
	return bytes;
}

var parseIPv6 = function (addr_str) {
	// IPv6 address
	var index    = 0
	var items    = []
	var fill_pos = undefined

	while (index < addr_str.length) {
		text = addr_str.substring(index);
		if (text.substring(0, 2) == '::') {
			if (fill_pos != undefined) throw "IPv6 Error: can't have two '::'";
			fill_pos = items.length;
			index    += 2;
			continue;
		}
		pos = text.indexOf(':');
		if (pos == 0) throw "IPv6 Error: missing ':'";
		if (pos != -1) {
			items.push(text.substring(0, pos));
			if (text.substring(pos, pos+2) == '::') {
				index += pos;
			} else {
				index += pos+1;
			}

			if (index == addr_str.length) throw "IPv6 Error: Invalid";
		} else {
			items.push(text);
			break
		}
	}

	if (items.length > 0 && items[items.length-1].indexOf('.') > -1) {
		// IPv4 address
		if (fill_pos != undefined && !(fill_pos <= items.length-1)) {
			throw "IPv6 Error: invalid IPv4 representation";
		}
		ipv4  = parseIPv4(items[items.length-1])
		items = new Array().concat(items.slice(0,items.length-1),
		                           [((ipv4[0]<<8) + ipv4[1]).toString(16)],
		                           [((ipv4[2]<<8) + ipv4[3]).toString(16)]);
	}

	if (fill_pos != undefined) {
		diff = 8 - items.length;
		if (diff <= 0) throw "IPv6 Error: found '::' but no sections skipped";
		filler = [];
		for (i=0; i<8; i++) { filler.push(0); }
		items = new Array().concat(items.slice(0, fill_pos),
		                           filler.slice(0, diff),
		                           items.slice(fill_pos, items.length));
	}

	if (items.length != 8) throw "IPv6 Error: too short";

	for (i in items) {
		items[i] = parseInt(items[i], 16);
	}

	return items;
}

var getHex = function (num) {
	return num.toString(16);
}

var getFullHex = function (num) {
	val = getHex(num);
	while (val.length < 4) {
		val = '0' + val;
	}
	return val;
}

var printIPv4_helper = function (ip) {
	bytes = []
	bytes.push(ip[6]>>8);
	bytes.push(ip[6]&0xff);
	bytes.push(ip[7]>>8);
	bytes.push(ip[7]&0xff);
	return bytes;
}

var printIPv4 = function (ip) {
	return printIPv4_helper(ip).join('.');
}

var printFullIPv4 = function (ip) {
	bytes = printIPv4_helper(ip);
	out   = [];
	for (b in bytes) {
		val = bytes[b].toString();
		while (val.length < 3) {
			val = '0' + val;
		}
		out.push(val);
	}
	return out.join('.');
}

var printFullIPv6 = function (ip) {
	out = []
	for (i in ip) {
		out.push(getFullHex(ip[i]));
	}
	return out.join(':');
}

var printNormalIPv6 = function (ip) {
	out = []
	for (i in ip) {
		out.push(getHex(ip[i]));
	}
	return out.join(':');
}

var printCompressedIPv6 = function (ip, start, skip) {
	long_run       = 0;
	long_run_start = -1;
	run            = 0;
	run_start      = -1;
	for (i=0; i<9; i++) {
		if (i<8 && self.ip[i] == 0) {
			run++;
			if (run_start == -1) {
				run_start = i;
			}
		} else {
			if (run > long_run) {
				long_run       = run;
				long_run_start = run_start;
			}
			run       = 0;
			run_start = -1;
		}
	}

	out   = []
	start = long_run_start
	end   = start + long_run;
	for (i in ip) {
		if (i < start || i >= end) {
			out.push(getHex(ip[i]));
		} else if (i == start) {
			out.push(':');
		}
	}
	return out.join(':').replace(':::', '::');
}


IP = function (addr, version) {
	if (!(this instanceof IP)) return new IP(addr, version);

	var self = this;

	if (version == "undefined") {
		self.version = 0;
	}


	// represent IP address as 8 16 bit ints (which are floats in reality)
	self.ip = [];
	for (i=0; i<8; i++) { self.ip.push(0); }

	if (typeof(addr) == 'string') {

		if (addr.substring(0, 2) == '0x') {
			// Hex value as string
			var rest = addr.substring(2);
			for (i=0; i<Math.min(rest.length, 32); i+=4) {
				end = rest.length-i;
				start = Math.max(rest.length-4-i, 0);
				substr = rest.substring(start, end);
				self.ip[7-(i/4)] = parseInt(substr, 16);
			}
			self.version = 6;

		} else if (addr.indexOf(':') > -1) {
			self.ip = parseIPv6(addr);
			self.version = 6;

		} else if (addr.indexOf('.') > -1) {
			v4 = compactIPv4(parseIPv4(addr));
			self.ip[6] = v4[0];
			self.ip[7] = v4[1];
			if (self.version == 6) {
				// user wants this to be a IPv6 address, but we
				//  need to convert an ipv4 address
				self.ip[5] = 0xffff;
			} else {
				self.version = 4;
			}
		}

	}

	self.str = function () {
		if (self.version == 4) {
			return printIPv4(self.ip);

		} else if (self.version == 6) {

			if (self.ip[0] == 0 &&
			    self.ip[1] == 0 &&
			    self.ip[2] == 0 &&
			    self.ip[3] == 0 &&
			    self.ip[4] == 0 &&
			    self.ip[5] == 0xffff) {
				// ipv4 address as ipv6 address
				return "::ffff:" + printIPv4(self.ip);

			} else {
				return printCompressedIPv6(self.ip);

			}
		}
	}

	self.fullStr = function () {
		if (self.version == 4) {
			return printFullIPv4(self.ip);

		} else if (self.version == 6) {
			if (self.ip[0] == 0 &&
			    self.ip[1] == 0 &&
			    self.ip[2] == 0 &&
			    self.ip[3] == 0 &&
			    self.ip[4] == 0 &&
			    self.ip[5] == 0xffff) {
				// ipv4 address as ipv6 address
				return "0000:0000:0000:0000:0000:ffff:" + printFullIPv4(self.ip);

			} else {
				return printFullIPv6(self.ip);

			}
		}
	}

	// If ipv4, print ipv4
	// If ipv6 and looks like ipv4, print ipv4
	// Else, print ipv6
	self.pureStr = function () {
		if (self.version == 4) {
			return printIPv4(self.ip);

		} else if (self.version == 6) {

			if (self.ip[0] == 0 &&
			    self.ip[1] == 0 &&
			    self.ip[2] == 0 &&
			    self.ip[3] == 0 &&
			    self.ip[4] == 0 &&
			    self.ip[5] == 0xffff) {
				// ipv4 address as ipv6 address
				return printIPv4(self.ip);

			} else {
				return printCompressedIPv6(self.ip);

			}
		}
	}

	self.hex = function () {
		if (self.vesrsion == 4) {
			out = "0x";
			out += getHex(self.ip[6]);
			out += getFullHex(self.ip[7]);
			return out;

		} else if (self.version == 6) {
			out = "0x";
			have_content = false;
			for (i=0; i<8; i++) {
				if (!have_content) {
					val = getHex(self.ip[i]);
					if (val != "0") {
						out += val;
						have_content = true;
					}
				} else {
					out += getFullHex(self.ip[i]);
				}
			}
			return out;
		}
	}

}

module.exports = IP;

/*
console.log(IP('67::ffff:8a:9c').str());
console.log(IP('67:ffff:8a:9c::5').str());
console.log(IP('0xffff8dd46ef5').str());
console.log(IP('::ffff:192.168.1.1').str());
console.log(IP('192.255.9.10').str());

console.log(IP('67::ffff:8a:9c').fullStr());
console.log(IP('67:ffff:8a:9c::5').fullStr());
console.log(IP('0xffff8dd46ef5').fullStr());
console.log(IP('::ffff:192.168.1.1').fullStr());
console.log(IP('192.255.9.10').fullStr());

*/

});
require("/jsIP.js");
