from django.shortcuts import render
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from attendancesheet import AttendanceSheet



def pdfgen(request):
    response = HttpResponse(content_type = "application/pdf")
    response['Content-Disposition'] = 'attachment; filename="somefilename.pdf"'
    
    sheet = AttendanceSheet( student_names = ["Bob", "Joe", "Mary", "Ann"], status_labels = ["Present", None, None, "Absent"], title = "Class Name")
    sheet.make_canvas(response)
    return response

#Status Label and organisation mapping CRUD


# Create your views here.
