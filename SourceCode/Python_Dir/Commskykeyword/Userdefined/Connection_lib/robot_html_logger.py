#  $Id $

"""
This module is a tools to reduce the size of robot log files. it 
catch all log of the keyword output. it's generate a HTML log file
for every keyword, and save a link to the keywords log in test case log files.

it's not use dynamic library to catch output log, because that can't catch the log
of robot. (like: arguments, return)

"""

import os
import cStringIO
import threading
import robot
from robot.output.xmllogger import XmlLogger

import robot.utils as utils
from xml.sax.saxutils import XMLGenerator

INITED_HOOKER = None

class BufferXMLGenerator(XMLGenerator):
    def startElement(self, name, attrs):
        if name != "robot":
            XMLGenerator.startElement(self, name, attrs)

    def endElement(self, name):
        if name != "robot":
            XMLGenerator.endElement(self, name)
        
def buffer_supported_xmlwrite_init(self, path):
    self.path = path
    if path.startswith("buf:"):
        self._output = cStringIO.StringIO()
        self._writer = BufferXMLGenerator(self._output, 'UTF-8')
    else:
        import os
        if os.path.exists(path):
            #echo("can't overwriting file:%s\n" % path)
            #raise Exception, "can't overwriting file:%s" % path
            pass
        
        self._output = open(path, 'wb') 
        self._writer = XMLGenerator(self._output, 'UTF-8')
        self._writer.startDocument()

from robot.running import Keyword

def run_and_caching_namespace(self, output, namespace):
    self.cached_namespace = namespace
    return self._origin_run(output, namespace)
    
def lazy_doc_acess(self):
    doc = self.cached_namespace.get_handler(self.handler_name)._method.__doc__
    return doc != '' and doc.splitlines()[0] or ''
    
def setup_lazy_doc_access_mechanism():
    Keyword._origin_run = Keyword.run
    Keyword.run = run_and_caching_namespace
    Keyword.lazy_doc_acess = lazy_doc_acess
        
def RobotLogHooker():
    global INITED_HOOKER
    if INITED_HOOKER == None and robot.output.OUTPUT:
        setup_lazy_doc_access_mechanism()
        XmlWriter.__init__ = buffer_supported_xmlwrite_init
        INITED_HOOKER = _RobotOutputHooker(robot.output.OUTPUT)
    return INITED_HOOKER

class _RobotOutputHooker(object):
    def __init__(self, output):
        self.output = output
                
        self.keyword_logger = []
        
        self.inited_log_viewer = False
        self._max_logsize = None #self._get_logsize()
        self._output_dir = None #self._get_logsize()
        self._work_dir = ""
        self._log_file = None
        self.file_name = None
        
        self.robot_variables = robot.variables.GLOBAL_VARIABLES
        self.html_output_idgen = utils.IdGenerator()
        
        self.html_output_idgen._ids['kw'] = 900000
        #self.failed_keyword = set()
        
        self.add_hook(self.output, "start_keyword", "end_keyword", "start_test")
    
    def add_hook(self, o, *args):
        for n in args:
            old = getattr(o, n)
            setattr(o, n, getattr(self, n))
            setattr(o, "_%s" % n, old)
    
    def max_logsize(self):
        if self._max_logsize is None:
            try:
                var_evaluator = self.robot_variables.replace_string
                self._max_logsize = int(var_evaluator("${logsize}"))
            except:
                self._max_logsize = 0
        
        return self._max_logsize
        
    def get_outputdir(self):
        if self._output_dir is None:
            try:
                var_evaluator = self.robot_variables.replace_string
                out_file = var_evaluator("${OUTPUT_FILE}")
                self._work_dir = os.path.dirname(out_file)

                out_file = os.path.basename(out_file)
                self._output_dir = os.path.splitext(out_file)[0]               
            except:
                self._output_dir = "output_"
            
            out_dir = os.path.join(self._work_dir, self._output_dir)
            if not os.path.exists(out_dir):
                os.mkdir(out_dir)
                
            self.copy_viewer_to_directory(out_dir)

        return self._output_dir
    
    def enable_bug_tracker(self):
        try:
            var_evaluator = self.robot_variables.replace_string
            tracker = var_evaluator("${BUG_TRACKER}")
            return tracker == '1'
        except:
            return 0
        

    def get_log_file(self):
        if self._log_file is None:
            var_evaluator = self.robot_variables.replace_string
            self._log_file = var_evaluator("${LOG_FILE}")
            if self._log_file is None or not self._log_file.endswith(".html"):
                self._log_file = "log.html"
                
            self._log_file = "%s/%s" % (self.get_outputdir(),
                                        os.path.basename(self._log_file))
            #echo("log file:%s\n" % self._log_file)

        return self._log_file
        
    def insert_log_viewer(self, logger):
        link_msg = ''
        
        if self.max_logsize() > 0:
            base_dir = self.get_outputdir()
            link_msg = '<applet id="log_viewer" code="org.robot.log.LogViewerApplet.class" MAYSCRIPT ' + \
                        ' archive="%s/logviewer-0.1.jar" width="1px" height="1px" ></applet>' % base_dir
                        
            link_msg += '<script type="text/javascript" ' + \
                       'src="%s/log_viewer.js" ></script>' % base_dir
                
        logger.message(Message(link_msg, 'INFO', True))
    
    def copy_viewer_to_directory(self, dir):
        import shutil
        base_dir = os.path.dirname(__file__)
        file = os.path.join(dir, 'logviewer-0.1.jar')
        if not os.path.exists(file):
            shutil.copy(os.path.join(base_dir, 'logviewer-0.1.jar'), file)

        file = os.path.join(dir, 'log_viewer.js')
        if not os.path.exists(file):
            shutil.copy(os.path.join(base_dir, 'log_viewer.js'), file)
    
    
    def merge_logger(self, parent, sub, kw):
        buffer = sub._writer._output.getvalue()
        if len(buffer) < self.max_logsize() or kw.status != 'PASS':
            #write buffered log to parent
            parent._writer._writer._write(buffer)
        else:
            if self.file_name is None:
                self.file_name = FileNameGenerator(self.get_log_file())

            save_as = self.file_name.get_name()
            try:
                self.convert_xml_log_to_html(buffer, save_as)
            except:
                import sys
                type, value, traceback = sys.exc_info()
                echo(str(value))
                #traceback.print_exc()
                pass
            link_path = "%s" % (save_as)
            link_msg = '<a href="%s" target="blank">%s</a>'%(link_path, link_path)
            parent.message(Message(link_msg, 'INFO', True))
        
    def convert_xml_log_to_html(self, xml_log, save_as=""):
        #echo("save_as:%s\n" % (save_as))
        #import robot.utils as utils
        keyword_wrapper = """
            <kw type="kw" name="dummy" timeout="">
            <doc>dummy.</doc>
            <arguments>
            </arguments>
            %s
            <status status="PASS" endtime="20081116 00:19:46.765" starttime="20081116 00:19:46.765"></status>
            </kw>
            """
        
        root_node = utils.DomWrapper(None, keyword_wrapper % xml_log)
        output = open(os.path.join(self._work_dir, save_as), 'wb')
        from robot.output.readers import Keyword
        serializer = KeywordSerializer(output, self.html_output_idgen)
        kw = Keyword(root_node)
        for child in kw.children:
            child.serialize(serializer)    
        #output.write(xml_log)
        output.close()
    
    def start_keyword(self, kw):
        # self._start_keyword(kw)
        
        attrs = { 'name': kw.name, 'type': kw.type, 'timeout': kw.timeout }
        self.output.listeners.start_keyword(kw)
        self.output.logger._writer.start_element('kw', attrs)
        # self.output.logger._writer.whole_element('doc', kw.doc)
        if not hasattr(self, 'cached_kws'):
            self.cached_kws = []
        self.cached_kws.append(kw)
        self.output.logger._write_list('arg', [utils.unic(a) for a in kw.args], 'arguments')
        
        try:
            if not self.inited_log_viewer:
                self.insert_log_viewer(self.output.logger)
                self.inited_log_viewer = True
            
            if self.max_logsize() > 0:                     
                self.keyword_logger.append(self.output.logger)
                self.output.logger = XmlLogger("buf:01")
        except:
            import sys
            type, value, traceback = sys.exc_info()
            echo(str(value))
            raise            
            
    def end_keyword(self, kw):
        try:
            if self.max_logsize() > 0:
                self.merge_logger(self.keyword_logger[-1], self.output.logger, kw)
                
                self.output.logger.close()
                self.output.logger = self.keyword_logger.pop()
                
        except:
            import sys
            type, value, traceback = sys.exc_info()
            echo(str(value))
            raise
        
        if hasattr(self, 'cached_kws') and self.cached_kws:
            try:
                self.output.logger._writer.whole_element('doc', self.cached_kws[-1].lazy_doc_acess())
            except:
                self.output.logger._writer.whole_element('doc', self.cached_kws[-1].doc)
            self.cached_kws.pop()
                
        self._end_keyword(kw)
        
    def start_test(self, test):
        self._start_test(test)
        self.inited_log_viewer = False
                                
    def __getattr__(self, name):
        return getattr(self.output, name)


def echo(msg):
    import sys
    sys.__stdout__.write(msg)
