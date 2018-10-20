'''

'''

import logging
import os
from flask import Flask, request, Response, \
  send_from_directory, jsonify, render_template
from flask_headers import headers
import requests
import requests.utils
import urllib3.contrib.pyopenssl
from d1_common import resource_map

urllib3.contrib.pyopenssl.inject_into_urllib3()

APPINFO = {"name": "d1_examples",
           "version": "2.0.0",
           }

DATAONE_HOME = os.path.expanduser(os.path.join("~", ".dataone"))
CHUNK_SIZE = 1024
CERTIFICATE_FOLDER = "certificates"
CACHE_FOLDER = "cache"

ENVIRONMENTS = {'production': {'home': os.path.join(DATAONE_HOME, 'env', 'production'),
                               'baseurl': 'https://cn.dataone.org/cn',
                               'login': 'https://cilogon.org/?skin=dataone',
                               'certificate': 'client_cert.pem',
                               'admin': 'cnode_cert.pem',
                               'cache_db': 'cache.sql3',
                               },
                'stage': {'home': os.path.join(DATAONE_HOME, 'env', 'stage'),
                          'baseurl': 'https://cn-stage.test.dataone.org/cn',
                          'login': 'https://cilogon.org/?skin=DataONEStage',
                          'certificate': 'client_cert.pem',
                          'admin': 'stage_cnode_cert.pem',
                          'cache_db': 'stage_cache.sql3',
                          },
                'stage-2': {'home': os.path.join(DATAONE_HOME, 'env', 'stage-2'),
                            'baseurl': 'https://cn-stage-2.test.dataone.org/cn',
                            'login': 'https://cilogon.org/?skin=DataONEStage2',
                            'certificate': 'client_cert.pem',
                            'admin': 'stage2_cnode_cert.pem',
                            'cache_db': 'stage2_cache.sql3',
                            },
                'sandbox': {'home': os.path.join(DATAONE_HOME, 'env', 'sandbox'),
                            'baseurl': 'https://cn-sandbox.test.dataone.org/cn',
                            'login': 'https://cilogon.org/?skin=DataONESandbox',
                            'certificate': 'client_cert.pem',
                            'admin': 'sandbox_cnode_cert.pem',
                            'cache_db': 'sandbox_cache.sql3',
                            },
                'sandbox-2': {'home': os.path.join(DATAONE_HOME, 'env', 'sandbox-2'),
                              'baseurl': 'https://cn-sandbox-2.test.dataone.org/cn',
                              'login': 'https://cilogon.org/?skin=DataONESandbox2',
                              'certificate': 'client_cert.pem',
                              'admin': 'sandbox2_cnode_cert.pem',
                              'cache_db': 'sandbox2_cache.sql3',
                              },
                'dev': {'home': os.path.join(DATAONE_HOME, 'env', 'dev'),
                        'baseurl': 'https://cn-dev.test.dataone.org/cn',
                        'login': 'https://cilogon.org/?skin=DataONEDev',
                        'certificate': 'client_cert.pem',
                        'admin': 'dev_cnode_cert.pem',
                        'cache_db': 'dev_cache.sql3',
                        },
                'dev-2': {'home': os.path.join(DATAONE_HOME, 'env', 'dev-2'),
                          'baseurl': 'https://cn-dev-2.test.dataone.org/cn',
                          'login': 'https://cilogon.org/?skin=DataONEDev2',
                          'certificate': 'client_cert.pem',
                          'admin': 'dev2_cnode_cert.pem',
                          'cache_db': 'dev2_cache.sql3',
                          },
                }

def initializeEnvironmentFolders():
  logging.info("Initializing environment state folders")
  for envname in list(ENVIRONMENTS.keys()):
    logging.info("%s environment" % envname)
    env = ENVIRONMENTS[envname]
    fdest = env['home']
    if not os.path.exists(fdest):
      logging.info("Creating home for %s environment", fdest)
      os.makedirs(fdest)
    fdest = os.path.join(env['home'], CERTIFICATE_FOLDER)
    if not os.path.exists(fdest):
      logging.info("Creating certificate folder for %s environment", fdest)
      os.makedirs(fdest)
      os.chmod(fdest, 0o700)
    fdest = os.path.join(env['home'], CACHE_FOLDER)
    if not os.path.exists(fdest):
      logging.info("Creating cache folder for %s environment", fdest)
      os.makedirs(fdest)


def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__,
              instance_relative_config=True,
              static_url_path='/static')
  # ensure the instance folder exists
  try:
    os.makedirs(app.instance_path)
  except OSError:
    pass

  logging.basicConfig(level=logging.DEBUG)

  def sendError(req, method, msg, status_code):
    err = "<error"
    err += " request='" + req + "'"
    err += " method='" + method + "'"
    err += ">" + msg + "</error>\n"
    return err, status_code


  def saveRequest(request):
    req_data = {}
    req_data['endpoint'] = request.endpoint
    req_data['method'] = request.method
    req_data['cookies'] = request.cookies
    req_data['data'] = request.data
    req_data['headers'] = dict(request.headers)
    req_data['headers'].pop('Cookie', None)
    req_data['args'] = request.args
    req_data['form'] = request.form
    req_data['remote_addr'] = request.remote_addr
    req_data['values'] = []
    for k in request.values:
      req_data['values'].append([k, request.values[k]])
    files = request.files.getlist("file[]")
    req_data['files'] = files
    return req_data


  @app.route('/version')
  def versionInfo():
    logging.debug("versionInfo call")
    return jsonify(APPINFO)



  @app.route('/', defaults={'path': 'index.html'})
  @app.route('/<path:path>')
  @headers({'Access-Control-Allow-Origin':'*'})
  def root(path):
    if path == 'favicon.ico':
      return sendError('',request.method,'Not Found', 404)
    return render_template(path)


  @app.route('/ore.html', defaults={'pid': ''})
  @app.route('/ore.html/<path:pid>')
  @headers({'Access-Control-Allow-Origin':'*'})
  def oreProcess(pid):
    logging.debug("ore.html, pid = " + pid)
    return render_template('ore.html', pid=pid)


  @app.route('/status/__ajaxproxy/<path:target>', methods=['GET', 'POST', ])
  @headers({'Access-Control-Allow-Origin':'*'})
  def proxyNodeStatus(target):
    return proxyNode(target)


  @app.route('/__ajaxproxy/<path:target>', methods=['GET', 'POST', ])
  @headers({'Access-Control-Allow-Origin':'*'})
  def proxyNode(target):
    if target == '':
      return "<error>/__ajaxproxy/...</error>", 404
    target = requests.utils.unquote(target)
    logging.debug("Requesting URL = %s", target)
    cert = None
    if request.method == 'GET':
      try:
        r = requests.get(target,
                         stream=True,
                         allow_redirects=False,
                         params=request.args,
                         cert=cert,
                         timeout=10)
      except requests.exceptions.Timeout as e:
        return "<error>/__ajaxproxy/...</error>", 500
      headers = dict(r.headers)
      if r.status_code in [302, 303]:
        r.status_code = 200
    elif request.method == 'POST':
      data = []
      for k in request.form:
        data.append((k, (k, request.form[k])))

      r = requests.post(target,
                        stream=True,
                        allow_redirects=False,
                        params=request.args,
                        files=data,
                        cert=cert)
      headers = dict(r.headers)
      if r.status_code in [302, 303]:
        r.status_code = 200

    def generate():
      for chunk in r.iter_content(CHUNK_SIZE):
        logging.debug(chunk)
        yield chunk

    # if 'location' in headers:
    #  headers.pop('location', None)
    logging.debug(headers)

    return Response(generate(), status=r.status_code)


  def processResourceMap(ore_text):
    '''
    '''
    oredoc = resource_map.ResourceMap()
    try:
      oredoc.deserialize(data=ore_text)
    except Exception as e:
      return sendError('/oreparse', '?', str(e))
    results = {
      'aggregated': [],
      'science_metadata': [],
      'science_data': [],
    }
    results['aggregated'] = oredoc.getAggregatedPids()
    results['science_metadata'] = oredoc.getAggregatedScienceMetadataPids()
    results['science_data'] = oredoc.getAggregatedScienceDataPids()
    return jsonify(results), 200


  @app.route('/oreparse/', methods=['GET', 'POST', ])
  @headers({'Access-Control-Allow-Origin':'*'})
  def parseResourceMap():
    '''
    given GET | POST ore=ORE-Identifier

    Returns: JSON listing:
      aggregated: all PIDs,
      science_metadata: metadata PIDs,
      science_data: data PIDs
    '''
    logging.debug("Method = " + request.method)
    logging.debug("Values = " + str(saveRequest(request)))
    if request.method == 'GET':
      target = request.values.get('ore', '')
      if target == '':
        return sendError('/oreparse/', 'GET', 'No target resource in request path', 404)
      logging.debug("Requesting URL = %s", target)
      cert = None
      try:
        r = requests.get(target,
                         allow_redirects=False,
                         params=request.args,
                         cert=cert,
                         timeout=15)
      except requests.exceptions.Timeout as e:
        return sendError('/oreparse/', 'GET', 'Request to source timed out', 504)
      headers = dict(r.headers)
      if r.status_code in [302, 303]:
        r.status_code = 200
      return processResourceMap(r.content)
    elif request.method == 'POST':
      ore_doc = None
      ore_stream = request.files.get('ore', None)
      if ore_stream is None:
        ore_doc = request.values.get('ore', None)
      else:
        ore_doc = ore_stream.stream.read()
      if ore_doc is None:
        return sendError('/oreparse/', 'POST', 'Expected RDF-XML in ore POST parameter.', 400)
      return processResourceMap(ore_doc)
    return sendError('/oreparse/', request.method, 'Not supported', 405)

  return app


if __name__ == '__main__':
  app = create_app()
  logging.basicConfig(level=logging.DEBUG)
  initializeEnvironmentFolders()
  app.run(debug=True)
