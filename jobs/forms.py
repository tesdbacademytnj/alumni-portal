from django import forms
from .models import (JobOpening, JobSeeker,
                     JOB_TYPE_CHOICES, OPENING_TYPE_CHOICES, EMPLOYMENT_STATUS_CHOICES,
                     JOINING_CHOICES, QUALIFICATION_CHOICES,
                     SALARY_NOT_DISCLOSED, SALARY_INDUSTRY_STANDARD,
                     format_years_experience)

CITY_CHOICES = [
    ('', '-- Select City --'),
    ('Chennai', 'Chennai'), ('Coimbatore', 'Coimbatore'), ('Madurai', 'Madurai'),
    ('Tiruchirappalli', 'Tiruchirappalli'), ('Salem', 'Salem'),
    ('Bangalore', 'Bangalore'), ('Mumbai', 'Mumbai'), ('Delhi', 'Delhi'),
    ('Hyderabad', 'Hyderabad'), ('Pune', 'Pune'), ('Kolkata', 'Kolkata'),
    ('Ahmedabad', 'Ahmedabad'), ('Kochi', 'Kochi'), ('Thiruvananthapuram', 'Thiruvananthapuram'),
    ('Others', 'Others'),
]

# Qualifications that need a course name
COURSE_REQUIRED_QUALS = {'Diploma', 'BE/BTech', 'ME/MTech', 'BCA', 'MCA', 'BSc', 'MSc', 'MBA', 'Others'}


class JobOpeningForm(forms.ModelForm):
    city                  = forms.ChoiceField(
        choices=CITY_CHOICES, required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'jobCity'}))
    city_other            = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter city or country — e.g. Chennai', 'id': 'jobCityOther', 'style': 'display:none'}))
    years_of_experience   = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 3 or 3+', 'id': 'jobYearsExp', 'style': 'display:none'}))
    salary_not_disclosed  = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'id': 'salaryNotDisclose', 'class': 'form-check-input'}))
    salary_industry_standard = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'id': 'salaryIndustryStandard', 'class': 'form-check-input'}))
    opening_type          = forms.ChoiceField(
        choices=OPENING_TYPE_CHOICES, required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'openingType'}))
    amount_to_pay         = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter amount to pay', 'id': 'amountToPay', 'style': 'display:none'}))
    backdoor_description  = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe the backdoor arrangement details...', 'id': 'backdoorDesc', 'style': 'display:none'}))

    class Meta:
        model  = JobOpening
        fields = ['title', 'company', 'domain', 'job_type', 'experience',
                  'years_of_experience', 'salary_package', 'city',
                  'last_date_to_apply', 'skills', 'description',
                  'opening_type', 'amount_to_pay', 'backdoor_description']

        widgets = {
            'title':                  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Python Developer'}),
            'company':                forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company Name'}),
            'domain':                 forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Web Development'}),
            'job_type':               forms.Select(attrs={'class': 'form-control'}),
            'experience':             forms.Select(attrs={'class': 'form-control', 'id': 'jobExp'}),
            'salary_package':         forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 10 LPA or 40000', 'id': 'id_salary_package'}),
            'last_date_to_apply':     forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'data-disable-past': 'true', 'placeholder': 'dd-mm-yyyy'}),
            'skills':                 forms.HiddenInput(),
            'description':            forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'id': 'jobDescription', 'placeholder': 'Paste or type the job description here — it will be auto-formatted into a professional layout.'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ('title', 'company', 'domain', 'job_type', 'experience',
                  'description', 'last_date_to_apply'):
            self.fields[f].required = True

    def clean(self):
        cd = super().clean()
        city = cd.get('city')
        if not city:
            raise forms.ValidationError("Please select a job location.")
        if city == 'Others' and not cd.get('city_other', '').strip():
            raise forms.ValidationError("Please enter the city name.")
        if city == 'Others':
            cd['city'] = cd['city_other'].strip()
        if cd.get('experience') == 'Experienced':
            years = cd.get('years_of_experience', '').strip()
            if not years:
                raise forms.ValidationError("Please enter years of experience required.")
            cd['years_of_experience'] = format_years_experience(years)

        last_date = cd.get('last_date_to_apply')
        if last_date:
            from django.utils import timezone
            if last_date < timezone.localdate():
                raise forms.ValidationError("Last date to apply cannot be in the past.")

        not_disclosed = cd.get('salary_not_disclosed')
        industry_standard = cd.get('salary_industry_standard')
        if not_disclosed and industry_standard:
            raise forms.ValidationError("Please choose only one salary option.")

        if not_disclosed:
            cd['salary_package'] = SALARY_NOT_DISCLOSED
        elif industry_standard:
            cd['salary_package'] = SALARY_INDUSTRY_STANDARD
        else:
            salary = cd.get('salary_package', '').strip()
            if not salary:
                raise forms.ValidationError(
                    "Please enter the salary/package, or choose 'Prefer not to disclose' or 'As per Industry Standard'.")
            import re
            num = re.sub(r'[^0-9.]', '', salary).rstrip('.')
            if num and re.match(r'^\d+(\.\d+)?$', num):
                if float(num) <= 100:
                    cd['salary_package'] = num + ' LPA'
                else:
                    cd['salary_package'] = '₹' + num

        if cd.get('opening_type') == 'Backdoor':
            if not cd.get('amount_to_pay', '').strip():
                raise forms.ValidationError("Please enter the amount to pay for backdoor opening.")
            if not cd.get('backdoor_description', '').strip():
                raise forms.ValidationError("Please describe the backdoor arrangement.")
        else:
            cd['amount_to_pay'] = ''
            cd['backdoor_description'] = ''
        return cd

    def save(self, commit=True):
        obj = super().save(commit=False)
        city = self.cleaned_data.get('city')
        obj.city = self.cleaned_data.get('city_other', '').strip() if city == 'Others' else city
        if commit:
            obj.save()
        return obj


class JobSeekerForm(forms.ModelForm):
    employment_status     = forms.ChoiceField(
        choices=EMPLOYMENT_STATUS_CHOICES, required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'seekStatus'}))
    years_of_experience   = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 3 or 3+', 'id': 'seekYearsExp'}))
    joining_preference    = forms.ChoiceField(
        choices=JOINING_CHOICES, required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'seekJoining'}))
    joining_months_others = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your joining preference', 'id': 'seekJoiningOther'}))
    salary_not_disclosed  = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'id': 'salaryToggle', 'class': 'form-check-input'}))
    qualification         = forms.ChoiceField(
        choices=QUALIFICATION_CHOICES, required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'seekQual'}))
    qualification_course  = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your course name', 'id': 'seekCourse'}))

    class Meta:
        model  = JobSeeker
        fields = ['title', 'email', 'mobile', 'qualification', 'qualification_course',
                  'employment_status', 'domain', 'experience', 'years_of_experience',
                  'joining_preference', 'joining_months_others',
                  'current_company', 'current_designation',
                  'expected_salary', 'salary_not_disclosed', 'current_city',
                  'skills', 'resume']
        widgets = {
            'title':               forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Desired Job Title / Role'}),
            'email':               forms.EmailInput(attrs={'class': 'form-control'}),
            'mobile':              forms.TextInput(attrs={'class': 'form-control'}),
            'domain':              forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Web Development'}),
            'experience':          forms.HiddenInput(),
            'current_company':     forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Current / Last Company', 'id': 'seekCompany'}),
            'current_designation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Current / Last Designation', 'id': 'seekDesig'}),
            'current_city':        forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Current City'}),
            'expected_salary':     forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 5 LPA', 'id': 'expectedSalary'}),
            'skills':              forms.HiddenInput(),
            'resume':              forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ('title', 'email', 'mobile', 'domain', 'current_city', 'skills'):
            self.fields[f].required = True
        self.fields['resume'].required = True

    def clean(self):
        cd = super().clean()
        status = cd.get('employment_status')
        if not status:
            raise forms.ValidationError("Please select your current employment status.")

        cd['experience'] = 'Fresher' if status == 'Fresher' else 'Experienced'
        is_fresher = status == 'Fresher'

        if not is_fresher:
            years = cd.get('years_of_experience', '').strip()
            if not years:
                raise forms.ValidationError("Please enter your years of experience.")
            cd['years_of_experience'] = format_years_experience(years)
            if not cd.get('current_company', '').strip():
                raise forms.ValidationError("Please enter your current/last company.")
            if not cd.get('current_designation', '').strip():
                raise forms.ValidationError("Please enter your current/last designation.")

        qual = cd.get('qualification')
        if qual in COURSE_REQUIRED_QUALS and not cd.get('qualification_course', '').strip():
            raise forms.ValidationError("Please enter your course name for the selected qualification.")

        joining = cd.get('joining_preference')
        if not joining:
            raise forms.ValidationError("Please select your joining preference.")
        if joining == 'Others' and not cd.get('joining_months_others', '').strip():
            raise forms.ValidationError("Please enter your joining preference details.")

        if not cd.get('salary_not_disclosed') and not cd.get('expected_salary', '').strip():
            raise forms.ValidationError("Please enter your expected salary or check 'Prefer not to disclose'.")
        if cd.get('salary_not_disclosed'):
            cd['expected_salary'] = 'Not Disclosed'

        if not cd.get('skills', '').strip():
            raise forms.ValidationError("Please add at least one skill.")

        return cd

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.employment_status     = self.cleaned_data.get('employment_status', '')
        obj.joining_preference    = self.cleaned_data.get('joining_preference', '')
        obj.joining_months_others = self.cleaned_data.get('joining_months_others', '')
        obj.qualification         = self.cleaned_data.get('qualification', '')
        obj.qualification_course  = self.cleaned_data.get('qualification_course', '')
        obj.years_of_experience   = self.cleaned_data.get('years_of_experience', '')
        if self.cleaned_data.get('salary_not_disclosed'):
            obj.expected_salary      = 'Not Disclosed'
            obj.salary_not_disclosed = True
        if commit:
            obj.save()
        return obj
