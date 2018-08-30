"use strict";

/**
 * Escape reserved characters in a SOLR query term and if necessary, wrap the 
 * entire string in quotes.
 *
 * @param v
 * @returns
 */
function SOLRencode(value) {
  var specials = ['+', '-', '&', '!', '(', ')', '{', '}', '[', ']', '^', '"', '~', '*', '?', ':', '\\'];
  var regexp = new RegExp("(\\" + specials.join("|\\") + ")", "g");
  var v = value.replace(regexp, "\\$1");
  if (v != value) {
    return '"' + v + '"';
  }
  return v;
}

/**
 * Encode a URI component 
 * @param v
 * @returns
 */
function URLencode(v) { 
  return encodeURIComponent(v);
}


// Add URL query KV pairs.
// url = base address
// args = associative array of K:V
// encode = if true, the URL encode the value
function addUrlQueryParams(url, args, encode) {
  var res = "";
  for (var key in args) {
    if (args[key].length > 0) {
      if (res.length > 0) {
        res += "&";
      }
      res += key + "=";
      if (encode) {
        res += URLencode(args[key]);
      } else {
        res += args[key];
      }
    }
  }
  if (res.length > 0) {
    return url + "?" + res;
  }
  return url;
}


function addSolrQueryParams(q, args) {
  var res = ""
  for (var key in args) {
    if (args[key].length > 0) {
      if (res.length > 0) {
        res += " AND "
      }
      if (key.startsWith("__")) {
        res += key.slice(2) + ":" + args[key];
      } else {
        res += key + ":" + SOLRencode(args[key]);
      }
    }
  }
  if (res.length > 0) {
    if (q == "*:*") {
      return res
    }
    return q + " AND " + res
  }
  return q
}


function encodeDate(sd) {
  try {
    var dt = Date.parse(sd);
    pd = dt.toISOString();
    return pd;
  }
  catch(err) {

  }
  return "";
}


function dateQuery(a, b) {
  if ((a === "" ) || (b === "")) {
    return "";
  }
  if ( a !== "NOW" ) {
    a = encodeDate(a);
  }
  if ( b !== "NOW" ) {
    b = encodeDate(b);
  }
  if ((a === "" ) || (b === "")) {
    return "";
  }
  return "[" + a + " TO " + b + "]";
}
