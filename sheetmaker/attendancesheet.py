'''
Created on Jun 11, 2016

@author: mike
'''

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.utils import simpleSplit
import unicodedata
from bidi.algorithm import get_display
from arabic_rtlize.process import rtlize

class AttendanceSheet(object):
    '''
    classdocs
    '''
    
    '''
    Width/Height of finder pattern squares : in pt as used by reportlab pdfgen
    '''
    FINDER_SIZE = 40
    
    '''
    Width of area (as measured from center of finder pattern to center of finder pattern) in pts
    '''
    AREA_WIDTH =  485
    
    '''
    Height of area (as measured from center of finder pattern to center of finder pattern) in pts
    '''
    AREA_HEIGHT = 722
    
    

    def __init__(self, student_names = [], page_size = A4, title = None, title_font = "Times-Roman", title_font_size = 16, label_font = "Helvetica", label_font_size = 11, area_width = 485, area_height = 722, finder_size = 40, om_diameter=16, om_spacing_x = 20.8, om_row_height = 20.651441242, om_offset_y = 31.6, om_offset_x_col1 = 12, om_offset_x_col2= 237.44, om_row_name_width = 144, num_rows = 33, status_labels = ["Present", "Late", "Excused", "Absent"]):
        '''
        Constructor
        
        All measurement units are in pts
        
        student_names - array of student names to be filled in
        page_size - page size tuple to use for reportlab pdf page
        title - page title displayed in header (e.g. the class name)
        title_font - the font name to use for the header
        title_font_size - the title font size
        label_font - the font name used for labels for student names and status_labels
        label_font_size - the font size used for labels
        area_width - Width of the area from finder pattern center to finder pattern center
        area_height - Height of the area from finder pattern center to finder pattern center
        finder_size - Width and Height of finder pattern squares
        om_size - Diameter of optical mark circles
        om_spacing_x - x axis distance from one optical mark center to the next
        om_row_height - y axis distance from one optical mark row to the next
        om_offset_y - y axis distance between center of top finder pattern and center of optical marks in row
        om_offset_x_col1 - x axis distance between center of left side finder patterns and start of the roll call number / student name
        om_offset_x_col2 - x axis distance between center of left side finder patterns and start of the second roll call number / student name
        num_rows - The number of rows in each column (we always do two columns)
        '''
        
        self.student_names = student_names
        self.page_size = page_size
        self.title = title
        self.title_font = title_font
        self.title_font_size = title_font_size
        self.label_font = label_font
        self.label_font_size = label_font_size
        self.area_width = area_width
        self.area_height = area_height
        self.finder_size = finder_size
        self.om_diameter = om_diameter
        self.om_spacing_x = om_spacing_x
        self.om_row_height = om_row_height
        self.om_offset_y = om_offset_y
        self.om_offset_x_col1 = om_offset_x_col1
        self.om_offset_x_col2 = om_offset_x_col2
        self.om_row_name_width = om_row_name_width
        self.num_rows = num_rows
        self.status_labels = status_labels
    
    
    
    def make_canvas(self, file, page_size = A4):
        '''
        Generates a new canvas with the given file
        object as its output
        '''
        p = Canvas(file, pagesize = page_size)
        self.render_to_canvas(p)
        p.save()
    
    def render_to_canvas(self, canvas):
        '''
        Render the sheet to a reportlab canvas
        '''
        margin_x = float(self.page_size[0] - self.area_width)/2
        margin_y = float(self.page_size[1] - self.area_height)/2
        
        #bottom left
        self._render_finder_pattern(canvas, margin_x, margin_y)
        #bottom right
        self._render_finder_pattern(canvas, self.page_size[0] - margin_x, margin_y)
        #top left
        self._render_finder_pattern(canvas, margin_x, self.page_size[1] - margin_y)
        #top right
        self._render_finder_pattern(canvas, self.page_size[0] - margin_x, self.page_size[1] - margin_y)
        
        om_start_y = self.page_size[1] - margin_y - self.om_offset_y - (self.om_row_height/2)
        om_offsets_x = [self.om_offset_x_col1, self.om_offset_x_col2]
        canvas.setFont(self.label_font, self.label_font_size)
        for i in range(len(om_offsets_x)):
            om_start_x = margin_x + om_offsets_x[i]
            for j in range(0, self.num_rows):
                name_index = (i*self.num_rows) + j
                name = ""
                if name_index < len(self.student_names) and self.student_names[name_index] is not None:
                    name = self.student_names[name_index]
                
                self._render_om_row(canvas, name_index+1, name, om_start_x, 
                                om_start_y - (j*self.om_row_height))
        
    
        #make the label headers
        for i in range(len(om_offsets_x)):
            label_start_x = margin_x + om_offsets_x[i] + self.om_row_name_width + (self.om_spacing_x/4)
            label_y = (self.page_size[1] - margin_y - self.om_offset_y) + (self.om_row_height/2) 
            
            for j in range(4):
                if self.status_labels[j]:
                    canvas.saveState()
                    canvas.translate(label_start_x + (j * self.om_spacing_x), label_y)
                    canvas.rotate(90)
                    canvas.drawString(0, 0, self.status_labels[j])
                    canvas.restoreState()
                    
        #Put the sheet title at the top - centered
        if self.title:
            title_width = stringWidth(self.title, self.title_font, self.title_font_size)
            canvas.setFont(self.title_font, self.title_font_size)
            canvas.drawString((self.page_size[0] - title_width)/2,
                          (self.page_size[1] - 18 - self.title_font_size),
                          self.title)
            
        canvas.showPage()
        
    def _render_om_row(self, canvas, line_number, name, x, y):
        '''
        Render an optical mark row
        canvas - the canvas to render to
        label - text to write (e.g. num - student name)
        x - left x coordinate
        y - bottom y coordinate
        '''
        canvas.setStrokeColorRGB(0, 0, 0)
        canvas.setLineWidth(1)
        label = "%s: %s" % (str(line_number), name)

        wrkText=unicode(label)

        isArabic=False
        isBidi=False
    
        for c in wrkText:
            cat=unicodedata.bidirectional(unicode(c))
    
            if cat=="AL" or cat=="AN":
                isArabic=True
                isBidi=True
                break
            elif cat=="R" or cat=="RLE" or cat=="RLO":
                isBidi=True
    
        if isArabic:
            wrkText=rtlize(wrkText)
	    name = rtlize(name)
	    #label = "%s: %s" % (str(line_number), name)
	    label = rtlize(label)
            #wrkText=arabic_rtlize.process.shape(wrkText)                    
    
        if isBidi:
            #wrkText=get_display(wrkText)
            pass
        
        label_width = stringWidth(wrkText, self.label_font, self.label_font_size)
        if label_width > self.om_row_name_width:
            #trim the middle initials
            names = name.split()
	    #names = wrkText.split()
            name = ""
            for index in range(len(names)):
                if index == 0 or index == len(names)-1:
                    name += names[index] + " "
                else:
                    name += names[index][:1] + ". "
	    label = simpleSplit("%s: %s" % (str(line_number), name), self.label_font, self.label_font_size, self.om_row_name_width)[0]
	    if isArabic:
		name = ""
	        for index in range(len(names)):
                    if index == 0 or index == len(names)-1:
                    	name += names[index] + " "
                    else:
                    	name += names[index][(len(names[index]) - 1):] + ". "
		
                    
                label = simpleSplit("%s :%s" % (name, str(line_number)), self.label_font, 
                                self.label_font_size, self.om_row_name_width)[0]
	    
             
        
        #canvas.drawString(x, y+2, wrkText)
	canvas.drawString(x, y+2, label)
        canvas.line(x, y, x + self.om_row_name_width - (self.om_diameter/2), y)
        
        om_x_start = x + self.om_row_name_width
        om_y = y + (self.om_row_height/2)
        for i in range(0, 4):
            if self.status_labels[i]:
                canvas.circle(om_x_start + (i * self.om_spacing_x), om_y,
                          self.om_diameter/2.0, fill = 0, stroke = 1)

        
    
    def _render_finder_pattern(self, canvas, x, y):
        '''
        Makes a QR code finder pattern at the given x/y coordinate
        on the given canvas
        '''
        dot_size = float(self.finder_size) / float(7)
        canvas.setStrokeColorRGB(0, 0, 0)
        canvas.setLineWidth(dot_size)
        canvas.setFillColorRGB(0, 0, 0)
        
        canvas.rect(x - (3*dot_size), y - (3*dot_size),
               6 * dot_size, 6* dot_size, fill = 0, stroke = 1)
        
        canvas.rect(x - (1.5*dot_size), y - (1.5*dot_size),
               3 * dot_size, 3*dot_size, fill = 1, stroke = 0)
        
    
