/* Build-time JSX transpile using the vendored Babel standalone, run under the
   JavaScriptCore shell that ships with macOS. No node, no npm, no install. */
var window = this, self = this, global = this;
var console = { log:function(){}, debug:function(){}, warn:function(){}, error:function(){}, info:function(){} };
var process = { env:{ NODE_ENV:"production" }, platform:"darwin", version:"v18.0.0", argv:[], cwd:function(){ return "/"; } };
var navigator = { userAgent:"jsc" };
var document = { createElement:function(){ return {}; }, querySelectorAll:function(){ return []; }, addEventListener:function(){} };

load("vendor/babel.js");

var args = arguments;              // [inFile, outFile]
var src = readFile(args[0]);
var res = Babel.transform(src, { presets:["react"], filename:args[0], compact:false, comments:true });
write(args[1], res.code);
print("transpiled " + args[0]);
