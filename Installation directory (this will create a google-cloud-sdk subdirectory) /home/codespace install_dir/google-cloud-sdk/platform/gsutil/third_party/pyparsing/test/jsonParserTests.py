# jsonParser.py
#
# Copyright (c) 2006, Paul McGuire
#

test1 = """
{
        "glossary": {
            "title": "example glossary",
                "GlossDiv": {
                        "title": "S",
                        "GlossList": [{
                "ID": "SGML",
                "SortAs": "SGML",
                "GlossTerm": "Standard Generalized Markup Language",
                "Acronym": "SGML",
                "LargestPrimeLessThan100": 97,
                "AvogadroNumber": 6.02E23,
                "EvenPrimesGreaterThan2": null,
                "PrimesLessThan10" : [2,3,5,7],
                "WMDsFound" : false,
                "IraqAlQaedaConnections" : null,
                "Abbrev": "ISO 8879:1986",
                "GlossDef":
"A meta-markup language, used to create markup languages such as DocBook.",
                "GlossSeeAlso": ["GML", "XML", "markup"],
                "EmptyDict" : {},
                "EmptyList" : []
            }]
        }
    }
}
"""

test2 = """
{"menu": {
  "id": "file",
  "value": "File:",
  "popup": {
    "menuitem": [
      {"value": "New", "onclick": "CreateNewDoc()"},
      {"value": "Open", "onclick": "OpenDoc()"},
      {"value": "Close", "onclick": "CloseDoc()"}
    ]
  }
}}
"""
test3 = """
{"widget": {
    "debug": "on",
    "window": {
        "title": "Sample Konfabulator Widget",        "name": "main_window",        "width": 500,        "height": 500
    },    "image": {
        "src": "Images/Sun.png",
        "name": "sun1",        "hOffset": 250,        "vOffset": 250,        "alignment": "center"
    },    "text": {
        "data": "Click Here",
        "size": 36,
        "style": "bold",        "name": "text1",        "hOffset": 250,        "vOffset": 100,        "alignment": "center",
        "onMouseUp": "sun1.opacity = (sun1.opacity / 100) * 90;"
    }
}}
"""
test4 = """
{"web-app": {
  "servlet": [    // Defines the CDSServlet
    {
      "servlet-name": "cofaxCDS",
      "servlet-class": "org.cofax.cds.CDSServlet",
/*
    Defines glossary variables that template designers
    can use across the site.  You can add new
    variables to this set by creating a new init-param, with
    the param-name prefixed with "configGlossary:".
*/
      "init-param": {
        "configGlossary:installationAt": "Philadelphia, PA",
        "configGlossary:adminEmail": "ksm@pobox.com",
        "configGlossary:poweredBy": "Cofax",
        "configGlossary:poweredByIcon": "/images/cofax.gif",
        "configGlossary:staticPath": "/content/static",
/*
    Defines the template loader and template processor
    classes.  These are implementations of org.cofax.TemplateProcessor
    and org.cofax.TemplateLoader respectively.  Simply create new
    implementation of these classes and set them here if the default
    implementations do not suit your needs.  Leave these alone
    for the defaults.
*/
        "templateProcessorClass": "org.cofax.WysiwygTemplate",
        "templateLoaderClass": "org.cofax.FilesTemplateLoader",
        "templatePath": "templates",
        "templateOverridePath": "",
/*
    Defines the names of the default templates to look for
    when acquiring WYSIWYG templates.  Leave these at their
    defaults for most usage.
*/
        "defaultListTemplate": "listTemplate.htm",
        "defaultFileTemplate": "articleTemplate.htm",
/*
    New! useJSP switches on JSP template processing.
    jspListTemplate and jspFileTemplate are the names
    of the default templates to look for when aquiring JSP
    templates.  Cofax currently in production at KR has useJSP
    set to false, since our sites currently use WYSIWYG
    templating exclusively.
*/
        "useJSP": false,
        "jspListTemplate": "listTemplate.jsp",
        "jspFileTemplate": "articleTemplate.jsp",
/*
    Defines the packageTag cache.  This cache keeps
    Cofax from needing to interact with the database
    to look up packageTag commands.
*/
        "cachePackageTagsTrack": 200,
        "cachePackageTagsStore": 200,
        "cachePackageTagsRefresh": 60,
/*
    Defines the template cache.  Keeps Cofax from needing
    to go to the file system to load a raw template from
    the file system.
*/
        "cacheTemplatesTrack": 100,
        "cacheTemplatesStore": 50,
        "cacheTemplatesRefresh": 15,
/*
    Defines the page cache.  Keeps Cofax from processing
    templates to deliver to users.
*/
        "cachePagesTrack": 200,
        "cachePagesStore": 100,
        "cachePagesRefresh": 10,
        "cachePagesDirtyRead": 10,
/*
    Defines the templates Cofax will use when
    being browsed by a search engine identified in
    searchEngineRobotsDb
*/
        "searchEngineListTemplate": "forSearchEnginesList.htm",
        "searchEngineFileTemplate": "forSearchEngines.htm",
        "searchEngineRobotsDb": "WEB-INF/robots.db",
/*
    New!  useDataStore enables/disables the Cofax database pool
*/
        "useDataStore": true,
/*
    Defines the implementation of org.cofax.DataStore that Cofax
    will use.  If this DataStore class does not suit your needs
    simply implement a new DataStore class and set here.
*/
        "dataStoreClass": "org.cofax.SqlDataStore",
/*
    Defines the implementation of org.cofax.Redirection that
    Cofax will use.  If this Redirection class does not suit
    your needs simply implenet a new Redirection class
    and set here.
*/
        "redirectionClass": "org.cofax.SqlRedirection",
/*
    Defines the data store name.   Keep this at the default
*/
        "dataStoreName": "cofax",
/*
    Defines the JDBC driver that Cofax's database pool will use
*/
        "dataStoreDriver": "com.microsoft.jdbc.sqlserver.SQLServerDriver",
/*
    Defines the JDBC connection URL to connect to the database
*/
        "dataStoreUrl": "jdbc:microsoft:sqlserver://LOCALHOST:1433;DatabaseName=goon",
/*
    Defines the user name to connect to the database
*/
        "dataStoreUser": "sa",
/*
    Defines the password to connect to the database
*/
        "dataStorePassword": "dataStoreTestQuery",
/*
    A query that will run to test the validity of the
    connection in the pool.
*/
        "dataStoreTestQuery": "SET NOCOUNT ON;select test='test';",
/*
    A log file to print out database information
*/
        "dataStoreLogFile": "/usr/local/tomcat/logs/datastore.log",
/*
    The number of connection to initialize on startup
*/
        "dataStoreInitConns": 10,
/*
    The maximum number of connection to use in the pool
*/
        "dataStoreMaxConns": 100,
/*
    The number of times a connection will be utilized from the
    pool before disconnect
*/
        "dataStoreConnUsageLimit": 100,
/*
    The level of information to print to the log
*/
        "dataStoreLogLevel": "debug",
/*
    The maximum URL length allowable by the CDS Servlet
    Helps to prevent hacking
*/
        "maxUrlLength": 500}},
/*
    Defines the Email Servlet
*/
    {
      "servlet-name": "cofaxEmail",
      "servlet-class": "org.cofax.cds.EmailServlet",
      "init-param": {
/*
    The mail host to be used by the mail servlet
*/
        "mailHost": "mail1",
/*
    An override
*/
        "mailHostOverride": "mail2"}},
/*
    Defines the Admin Servlet - used to refresh cache on
    demand and see statistics
*/
    {
      "servlet-name": "cofaxAdmin",
      "servlet-class": "org.cofax.cds.AdminServlet"},
/*
    Defines the File Servlet - used to display files like Apache
*/
    {
      "servlet-name": "fileServlet",
      "servlet-class": "org.cofax.cds.FileServlet"},
    {
      "servlet-name": "cofaxTools",
      "servlet-class": "org.cofax.cms.CofaxToolsServlet",
      "init-param": {
/*
    Path to the template folder relative to the tools tomcat installation.
*/
        "templatePath": "toolstemplates/",
/*
    Logging boolean 1 = on, 0 = off
*/
        "log": 1,
/*
    Location of log. If empty, log will be written System.out
*/
        "logLocation": "/usr/local/tomcat/logs/CofaxTools.log",
/*
    Max size of log in BITS. If size is empty, no limit to log.
    If size is defined, log will be overwritten upon reaching defined size.
*/
        "logMaxSize": "",
/*
    DataStore logging boolean 1 = on, 0 = off
*/
        "dataLog": 1,
/*
    DataStore location of log. If empty, log will be written System.out
*/
        "dataLogLocation": "/usr/local/tomcat/logs/dataLog.log",
/*
    Max size of log in BITS. If size is empty, no limit to log.
    If size is defined, log will be overwritten upon reaching defined size.
*/
        "dataLogMaxSize": "",
/*
    Http string relative to server root to call for page cache
    removal to Cofax Servlet.
*/
        "removePageCache": "/content/admin/remove?cache=pages&id=",
/*
    Http string relative to server root to call for template
    cache removal to Cofax Servlet.
*/
        "removeTemplateCache": "/content/admin/remove?cache=templates&id=",
/*
    Location of folder from root of drive that will be used for
    ftp transfer from beta server or user hard drive to live servers.
    Note that Edit Article will not function without this variable
    set correctly. MultiPart request relies upon access to this folder.
*/
        "fileTransferFolder": "/usr/local/tomcat/webapps/content/fileTransferFolder",
/*
    Defines whether the Server should look in another path for
    config files or variables.
*/
        "lookInContext": 1,
/*
    Number of the ID of the top level administration group in tblPermGroups.
*/
        "adminGroupID": 4,
/*
    Is the tools app running on  the 'beta server'.
*/
        "betaServer": true}}],
  "servlet-mapping": {
/*
    URL mapping for the CDS Servlet
*/
     "cofaxCDS": "/",
/*
    URL mapping for the Email Servlet
*/
     "cofaxEmail": "/cofaxutil/aemail/*",
/*
    URL mapping for the Admin servlet
*/
     "cofaxAdmin": "/admin/*",
/*
    URL mapping for the Files servlet
*/
     "fileServlet": "/static/*",
     "cofaxTools": "/tools/*"},
/*
    New! The cofax taglib descriptor file
*/
  "taglib": {
    "taglib-uri": "cofax.tld",
    "taglib-location": "/WEB-INF/tlds/cofax.tld"}}}

"""

test5 = """
{"menu": {
    "header": "SVG Viewer",
    "items": [
        {"id": "Open"},
        {"id": "OpenNew", "label": "Open New"},
        null,
        {"id": "ZoomIn", "label": "Zoom In"},
        {"id": "ZoomOut", "label": "Zoom Out"},
        {"id": "OriginalView", "label": "Original View"},
        null,
        {"id": "Quality"},
        {"id": "Pause"},
        {"id": "Mute"},
        null,
        {"id": "Find", "label": "Find..."},
        {"id": "FindAgain", "label": "Find Again"},
        {"id": "Copy"},
        {"id": "CopyAgain", "label": "Copy Again"},
        {"id": "CopySVG", "label": "Copy SVG"},
        {"id": "ViewSVG", "label": "View SVG"},
        {"id": "ViewSource", "label": "View Source"},
        {"id": "SaveAs", "label": "Save As"},
        null,
        {"id": "Help"},
        {"id": "About", "label": "About Adobe CVG Viewer..."}
    ]
}}
"""
