"use strict";

// Globals
var SERVICE_HOST = "examples.dataone.org";
var LOG_LEVEL = "info";
var FORM_DATA = null;  //This value is overwritten by the calling app. It
                       //holds the form data from the current UI to be stored
                       //in local storage.

String.prototype.endsWith = function(suffix) {
  /*
  Add endsWith support to String objects
   */
  return this.indexOf(suffix, this.length - suffix.length) !== -1;
};


function valueOrDefault(v, def) {
  if (typeof v != 'undefined') {
    return def;
  }
  return v;
}

function jq( myid ) {
  /*
  Escape an id value so that it can be used as a jquery ID selector
   */
  return "#" + myid.replace( /(:|\.|\[|\]|,)/g, "\\$1" );
}


function enableEnterKeyAction(dest_element) {
  /*
  Ties the press of the enter key to the getXML() operation.
   */
  $(document).keypress(function(e) {
    if (e.which === 13) {
      getXML($("#a_operation").text(), null, dest_element);
    }
  });
}


/**
 * Peform a Network Service Lookup, using StatDNS API.
 *
 * @param  nid    identifier of element that will be updated with answer
 * @param   dn    A well-formed domain name to resolve.
 */
function NSLookup(nid, dn) {
  var url = "https://examples.dataone.org/rrda/8.8.8.8:53/%FQDN%/a".replace("%FQDN%",dn);
  $.ajax({
    dataType: "json",
    url: url,
    async: true,
    success: function(response) {
      //console.log("nid = " + nid);
      //console.log(response)
      for (var i=0; i < response.answer.length; i++) {
        if (response.answer[i]['type'] == 'A') {
          $(jq(nid)).text(response.answer[i]['rdata']);
        }
      }
      $(nid).text("");
    },
  });
}



function parseURL(url) {
  /*
  Split a url into its component, returned as a dictionary
   */
  var parser = document.createElement('a');
  var searchObject = {};
  var queries;
  var split;
  var i;
  // Let the browser do the work
  parser.href = url;

  // Convert query string to object
  queries = parser.search.replace(/^\?/, '').split('&');
  for ( i = 0; i < queries.length; i++ ) {
    split = queries[i].split('=');
    searchObject[split[0]] = split[1];
  }
  return {
    protocol : parser.protocol,
    host : parser.host,
    hostname : parser.hostname,
    port : parser.port,
    pathname : parser.pathname,
    search : parser.search,
    searchObject : searchObject,
    hash : parser.hash
  };
}

/* Check the current location. If not served by localhost or
 examples.dataone.org, then change places.
 */
function enableProxy() {
  var curl = window.location.href;
  var parts = parseURL(curl);
  var pathparts;
  if ((parts.hostname === "localhost") ||
      (parts.hostname.startsWith("127.0.0")) ||
      (parts.hostname === SERVICE_HOST)) {
    return;
  }
  pathparts = parts.pathname.split("/");
  window.location.href = "https://" + SERVICE_HOST + "/" + pathparts[pathparts.length - 1];
}


function header() {
  var t = '<a href="index.html" id="nav_index">Index</a>';
  t += ' | <a href="nodes.html">listNodes</a>';
  t += ' | <a href="listformats.html">listFormats</a>';
  t += ' | <a href="listobjects.html">listObjects</a>';
  t += ' | <a href="sysmeta.html">getSystemMetadata</a>';
  t += ' | <a href="getobject.html">getObject</a>';
  t += ' | <a href="resolve.html">resolve</a>';
  t += ' | <a href="queryfields.html">queryEngineDescription</a>';
  t += ' | <a href="querycn.html">query</a>';
  t += ' | <a href="queryfieldvalues.html">query(Terms)</a>';
  t += ' | <a href="resource_find.html">explore package</a>';
  t += ' | <a href="echo_indexed_object.html">echo indexed object</a>';
  t += ' | <a href="pid.html">Get PID</a>';
  $("#index").append(t);
}

function serverList() {
  var servers = [
    ['Production', 'https://cn.dataone.org/cn'],
    ['Prod-UCSB', 'https://cn-ucsb-1.dataone.org/cn'],
    ['Prod-UNM', 'https://cn-unm-1.dataone.org/cn'],
    ['Prod-ORC', 'https://cn-orc-1.dataone.org/cn'],
    ['Stage', 'https://cn-stage.test.dataone.org/cn'],
    ['Stage-UCSB', 'https://cn-stage-ucsb-1.test.dataone.org/cn'],
    ['Stage-UNM', 'https://cn-stage-unm-1.test.dataone.org/cn'],
    ['Stage-ORC', 'https://cn-stage-orc-1.test.dataone.org/cn'],
    ['Stage-2', 'https://cn-stage-2.test.dataone.org/cn'],
    ['Stage-2-UNM', 'https://cn-stage-unm-2.test.dataone.org/cn'],
    ['Stage-2-ORC', 'https://cn-stage-orc-2.test.dataone.org/cn'],
    ['Sandbox', 'https://cn-sandbox.test.dataone.org/cn'],
    ['Sandbox-UCSB', 'https://cn-sandbox-ucsb-1.test.dataone.org/cn'],
    ['Sandbox-UNM', 'https://cn-sandbox-unm-1.test.dataone.org/cn'],
    ['Sandbox-ORC', 'https://cn-sandbox-orc-1.test.dataone.org/cn'],
    ['Sandbox-2', 'https://cn-sandbox-2.test.dataone.org/cn'],
    ['Sandbox-2-UCSB', 'https://cn-sandbox-ucsb-2.test.dataone.org/cn'],
    ['Dev', 'https://cn-dev.test.dataone.org/cn'],
    ['Dev-UCSB', 'https://cn-dev-ucsb-1.test.dataone.org/cn'],
    ['Dev-UNM', 'https://cn-dev-unm-1.test.dataone.org/cn'],
    ['Dev-ORC', 'https://cn-dev-orc-1.test.dataone.org/cn'],
    ['Dev-2', 'https://cn-dev-2.test.dataone.org/cn'],
    ['Dev-2-UCSB', 'https://cn-dev-ucsb-2.test.dataone.org/cn'],
    ['Dev-2-UNM', 'https://cn-dev-unm-2.test.dataone.org/cn']
    ];
  var i, t;
  for (i in servers) {

    t = "<option value='" + servers[i][1] + "'>" + servers[i][0] + "</option>";
    log.info(t);
    $('#sel_environment').append(t);
  }
}

function clearUI() {
  $(".output").html("&nbsp;");
  $("#extracted_values tr").remove();
}


function saveForm() {
  // index by page name

}


function restoreForm() {

}


function remember(pid, baseurl) {
  if (pid !== null) {
    localStorage.last_pid = pid;
  }
  if (baseurl !== null) {
    localStorage.last_environment = baseurl;
  }
}

function recall() {
  // if field already has a value, then don't override
  var current_val = $("#it_pid").val();
  try {
    if (! current_val.length > 0) {
      var pid = localStorage.last_pid;
      if (pid) {
        $("#it_pid").val(pid);
      }
    }    
  } catch(err) {
    console.log(err);
  }
  var last_environment = localStorage.last_environment;
  if (last_environment) {
    $('#sel_environment').val(last_environment);
    $("#in_baseurl").val(last_environment);
  }
}

function formatXml(xml, linenumbers) {
  var formatted = '';
  var line = 0;
  var reg = /(>)(<)(\/*)/g;
  var pad = 0;
  xml = xml.replace(reg, '$1\r\n$2$3');
  jQuery.each(xml.split('\r\n'), function(index, node) {
    var indent = 0;
    var padding = '';
    var i;
    if (node.match(/.+<\/\w[^>]*>$/)) {
      indent = 0;
    } else if (node.match(/^<\/\w/)) {
      if (pad != 0) {
        pad -= 1;
      }
    } else if (node.match(/^<\w[^>]*[^\/]>.*$/)) {
      indent = 1;
    } else {
      indent = 0;
    }

    if (linenumbers) {
      padding = line + ": ";
    }
    for (i = 0; i < pad; i++) {
      padding += ' ';
    }

    formatted += padding + node + '\r\n';
    line += 1;
    pad += indent;
  });
  return formatted;
}

function defaultXMLProcessing(xml, dest_element) {
  if ( typeof (processXML) == "function") {
    processXML(xml);
  }
  if (!dest_element) {
    dest_element = '#xml_output';
  }
  var sxml = new XMLSerializer();
  var doc = sxml.serializeToString(xml);
  $(dest_element).text(formatXml(doc, false));
  //$('#headers_output').text(headers);
}



function defaultJSONProcessing(data, dest_element) {
  console.log(data);
}


function getJSON(url, processfunc) {
  if ( typeof (processfunc) != "function") {
    processfunc = defaultJSONProcessing;
  }
  log.info("Loading " + url);
  var proxy = $(location).attr('protocol') + "//" + $(location).attr('host');
  proxy += "/__ajaxproxy/";
  var proxyurl = proxy + encodeURIComponent(url);
  $.ajax({
    type : "GET",
    url : proxyurl,
    dataType : "json",
    async : true,
    success : function(data) {
      processfunc(data);
    },
    error : function(jqXHR, textStatus, errorThrown) {
      if (jqXHR.status == 303) {
        log.info("Success, but redirect");
        var data = $.parseXML(jqXHR.responseText);
        processfunc(data);
      } else {
        log.error("Request failed: " + proxyurl);
        var msg = "Error(" + jqXHR.status + "): " + errorThrown;
        log.error(msg);
        msg += "\n";
        msg += jqXHR.responseText;
        console.log(msg);
      }
    }
  });
}



function getXML(url, processfunc, dest_element) {
  if (!dest_element) {
    dest_element = '#xml_output';
  }
  $(dest_element).empty();
  $(dest_element).text("Working...");
  $("#extracted_values").empty();
  if ( typeof (processfunc) != "function") {
    processfunc = defaultXMLProcessing;
  }
  log.info("Loading " + url);
  var proxy = $(location).attr('protocol') + "//" + $(location).attr('host');
  proxy += "/__ajaxproxy/";
  var proxyurl = proxy + encodeURIComponent(url);
  $.ajax({
    type : "GET",
    url : proxyurl,
    dataType : "xml",
    async : true,
    success : function(xml) {
      log.info("Success. Loading response xml to " + dest_element);
      $(dest_element).empty();
      processfunc(xml, dest_element);
    },
    error : function(jqXHR, textStatus, errorThrown) {
      $(dest_element).empty();
      if (jqXHR.status == 303) {
        log.info("Success, but redirect. Loading response xml to " + dest_element);
        var xml = $.parseXML(jqXHR.responseText);
        processfunc(xml, dest_element);
      } else {
        log.error("Request failed: " + proxyurl);
        var msg = "Error(" + jqXHR.status + "): " + errorThrown;
        log.error(msg);
        msg += "\n";
        msg += jqXHR.responseText;
        $(dest_element).text(msg);
      }
    }
  });
}


function getORE(url, processfunc, dest_element) {
  if (!dest_element) {
    dest_element = '#ore_output';
  }
  $(dest_element).empty();
  $(dest_element).text("Working...");
  $("#extracted_values").empty();
  if ( typeof (processfunc) != "function") {
    processfunc = defaultJSONProcessing;
  }
  log.info("Loading " + url);
  var proxy = $(location).attr('protocol') + "//" + $(location).attr('host');
  proxy += "/oreparse/";
  $.ajax({
    type : "GET",
    url : proxy,
    dataType : "json",
    data:{'ore':url},
    async : true,
    success : function(json) {
      log.info("Success. Loading response xml to " + dest_element);
      $(dest_element).empty();
      processfunc(json, dest_element);
    },
    error : function(jqXHR, textStatus, errorThrown) {
      $(dest_element).empty();
      if (jqXHR.status == 303) {
        log.info("Success, but redirect. Loading response xml to " + dest_element);
        var json = jqXHR.responseText;
        processfunc(json, dest_element);
      } else {
        log.error("Request failed: " + proxy);
        var msg = "Error(" + jqXHR.status + "): " + errorThrown;
        log.error(msg);
        msg += "\n";
        msg += jqXHR.responseText;
        $(dest_element).text(msg);
      }
    }
  });
}



function sortTable(table, order) {
  var asc = order === 'asc', tbody = table.find('tbody');
  tbody.find('tr').sort(function(a, b) {
    if (asc) {
      return $('td:first', a).text().localeCompare($('td:first', b).text());
    } else {
      return $('td:first', b).text().localeCompare($('td:first', a).text());
    }
  }).appendTo(tbody);
}


// Generate a curl command that can perform the operation
function generateCurl(url) {
  var res = "curl -s -k \"" + url + "\" | xml fo";
  return res;
}


/*
 Perform common UI initialization operations.
 Called at the start of jQuery(document).ready(function($) { ... }
 */
function initialize() {
  log.setLevel(LOG_LEVEL, false);
  enableProxy();
  header();
  clearUI();
  recall();
  doEncoding();
  $('#sel_environment').on('change', function() {
    $("#in_baseurl").val(this.value);
    doEncoding();
  });
  $("#toggle_help").click(function() {
    $(".help").toggle();
  });
  $(".url").click(function() {
    getXML($(this).text());
  });
  $("#sel_environment").focus();
  $(document).keypress(function(e) {
    if (e.which === 49 && e.ctrlKey) {
      $("#nav_index").focus();
    }
  });

}

