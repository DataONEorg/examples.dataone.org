
import logging
import requests
import json
from urllib.parse import quote
import dateutil.parser

PRODUCTION_SOLR = "https://cn.dataone.org/cn/v2/query/solr/"

# List of characters that should be escaped in solr query terms
SOLR_RESERVED_CHAR_LIST = [
    "+",
    "-",
    "&",
    "|",
    "!",
    "(",
    ")",
    "{",
    "}",
    "[",
    "]",
    "^",
    '"',
    "~",
    "*",
    "?",
    ":",
]


def escapeSolrQueryTerm(term):
    """
  Escape a solr query term for solr reserved characters
  Args:
    term: query term to be escaped

  Returns: string, the escaped query term
  """
    term = term.replace("\\", "\\\\")
    for c in SOLR_RESERVED_CHAR_LIST:
        term = term.replace(c, "\{}".format(c))
    return term


def quoteSolrTerm(term):
    """
  Return a quoted, escaped Solr query term
  Args:
    term: (string) term to be escaped and quoted

  Returns: (string) quoted, escaped term
  """
    return f'"{escapeSolrQueryTerm(term)}"'


def generateSchemaOrgGeo(nbc, ebc, sbc, wbc):
    if nbc == sbc:
        return {
            "@type":"GeoCoordinates",
            "latitude":nbc,
            "longitude": wbc
        }
    return {
        "@type":"GeoShape",
        "box":f"{wbc}, {sbc} {ebc}, {nbc}",
    }

def generateGeoJSONString(nbc, ebc, sbc, wbc):
    if nbc == sbc:
        return json.dumps({
            "type":"Point",
            "coordinates": [ebc, nbc],
        })
    if ebc < wbc:
        ebc = 360.0 - ebc
    g = {"type":"Feature",
         "properties":{},
         "geometry":{
            "type": "Polygon",
            "coordinates":[
                [wbc, sbc],
                [ebc, sbc],
                [wbc, nbc],
                [wbc, sbc],
            ]
         }}
    return json.dumps(g)

def getAuthorText(origin):
    if not isinstance(origin, list):
        return ""
    if len(origin) <= 0:
        return ""
    author_text = ""
    for i in range(0, len(origin)):
        if (i >= 5):
            return author_text + ", et al"
        if i > 0:
            if len(origin) > 2:
                author_text += ", "
            if i+1 == len(origin):
                author_text += " and"
            if len(origin) > 1:
                author_text += " "
        author_text += origin[i]
    return author_text

def getYearPublished(doc):
    date_str = doc.get("pubDate", None)
    if date_str is None:
        date_str = doc.get("dateUploaded")
    if date_str is None:
        return ""
    date_pub = dateutil.parser.parse(date_str)
    return str(date_pub.year)

def getCitationIdentifierText(doc, nodename):
    try:
        sid = doc["seriesId"]
        if nodename == "urn:node:PANGAEA":
            return sid
        return f"{sid}, version: {doc['identifier']}"
    except KeyError:
        pass
    return doc["identifier"]

class IDResolver(object):
    def __init__(self, solr_url=None, session=None):
        self._L = logging.getLogger(self.__class__.__name__)
        if solr_url is None:
            solr_url = PRODUCTION_SOLR
        self._solr_url = solr_url
        self._session = session

    def getSession(self):
        if self._session is None:
            self._session = requests.Session()
        return self._session

    def GET(self, params, url=None):
        if url is None:
            url = self._solr_url
        session = self.getSession()
        with session.get(url, params=params) as response:
            res = {
                "status": response.status_code,
                "body": response.text,
                "data": None,
            }
            if res["status"] == 200:
                try:
                    res["data"] = json.loads(res["body"])
                except json.JSONDecodeError as e:
                    pass
            return res

    def _get_doc_value(self, doc, name, default=None):
        """
        Given a doc, return element with name or default if not found.
        Args:
            name:
            default:

        Returns:
        """
        try:
            return doc[name]
        except KeyError:
            return default


    def getObjectJSONLD(self, an_id):

        def _getDatePublished(doc):
            try:
                return doc["pubDate"]
            except:
                pass
            try:
                return doc["dateUploaded"]
            except:
                pass
            return None

        def addTemporalCoverage(jsonld, doc):
            begin_date = doc.get("beginDate", None)
            end_date = doc.get("endDate", None)
            if begin_date is not None and end_date is not None:
                jsonld["temporalCoverage"] = f"{begin_date}/{end_date}"
            elif begin_date is not None:
                jsonld["temporalCoverage"] = begin_date
            elif end_date is not None:
                jsonld["temporalCoverage"] = end_date
            return jsonld

        def addSpatialcoverage(jsonld, doc):
            try:
                ebc = float(doc["eastBoundCoord"])
                wbc = float(doc["westBoundCoord"])
                nbc = float(doc["northBoundCoord"])
                sbc = float(doc["southBoundCoord"])
            except KeyError:
                return jsonld
            spat = {"@type":"Place",
                    "additionalProperty":[{"@type":"PropertyValue",
                                          "additionalType":"http://dbpedia.org/resource/Coordinate_reference_system",
                                          "name":"Coordinate Reference System",
                                          "value": "http://www.opengis.net/def/crs/OGC/1.3/CRS84",
                                          },],
                    "geo":generateSchemaOrgGeo(nbc,ebc,sbc,wbc),
                    "subjectOf": {
                        "@type":"CreativeWork",
                        "fileFormat":"application/vnd.geo+json",
                        "text":generateGeoJSONString(nbc,ebc,sbc,wbc),
                        }
                    }
            jsonld["spatialCoverage"] = spat
            return jsonld

        def addCitation(jsonld, doc):
            try:
                title = doc["title"]
                origin = doc["origin"]
                nodename = doc["datasource"]
            except KeyError:
                return jsonld
            parts = []
            parts.append(getAuthorText(origin))
            parts.append(getYearPublished(doc))
            parts.append(title)
            parts.append(nodename)
            parts.append(getCitationIdentifierText(doc, nodename))
            jsonld["citation"] = ". ".join(parts) + "."
            return jsonld

        def addElement(jsonld, doc, element, source, join=False):
            try:
                val = doc[source]
                if isinstance(val, list):
                    if join:
                        jsonld[element] = ",".join(val)
                    else:
                        jsonld[element] = val
                else:
                    jsonld[element] = val
            except KeyError:
                self._L.debug("No element %s available", element)
            return jsonld

        params = dict(wt="json",
                      fl="*",
                      )
        an_id_quoted = quoteSolrTerm(an_id)
        params["q"] = f"id:{an_id_quoted} OR seriesId:{an_id_quoted}"
        response = self.GET(params)
        jsonld = dict()
        if response["status"] != 200:
            return jsonld
        doc = response["data"]["response"]["docs"][0]
        logging.debug(str(doc))
        jsonld["@context"] = {"@vocab":"http://schema.org/",}
        jsonld["@type"] = "Dataset"
        jsonld["@id"] = f"https://dataone.org/datasets/{quote(an_id)}"
        jsonld["url"] = f"https://cn.dataone.org/cn/v2/resolve/{quote(an_id)}"
        jsonld["isAccessibleForFree"] = True
        jsonld["version"] = an_id
        jsonld["identifier"] = an_id
        jsonld["datePublished"] = _getDatePublished(doc)
        jsonld = addElement(jsonld, doc, "publisher", "datasource")
        jsonld = addElement(jsonld, doc, "name", "title")
        jsonld = addElement(jsonld, doc, "description", "abstract")
        jsonld = addElement(jsonld, doc, "creator", "origin")
        jsonld = addElement(jsonld, doc, "keywords", "", join=True)
        jsonld = addElement(jsonld, doc, "variablesMeasured", "attributeName")
        jsonld = addTemporalCoverage(jsonld, doc)
        jsonld = addSpatialcoverage(jsonld, doc)
        jsonld = addCitation(jsonld, doc)
        return jsonld