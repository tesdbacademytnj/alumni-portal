from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import CustomUser, INSTITUTE_CHOICES
import datetime

TAMIL_NADU_CITIES = [
    'Chennai', 'Coimbatore', 'Madurai', 'Tiruchirappalli', 'Salem',
    'Tirunelveli', 'Tiruppur', 'Ranipet', 'Nagercoil', 'Thanjavur',
    'Vellore', 'Kancheepuram', 'Erode', 'Thoothukudi', 'Dindigul',
    'Cuddalore', 'Karur', 'Nagapattinam', 'Pudukkottai', 'Ramanathapuram',
    'Virudhunagar', 'Namakkal', 'Krishnagiri', 'Dharmapuri', 'Perambalur',
    'Ariyalur', 'Sivaganga', 'Viluppuram', 'Kallakurichi', 'Chengalpattu',
    'Tenkasi', 'Tirupattur', 'Tiruvannamalai', 'The Nilgiris',
]

INDIA_CITIES = [
    'Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Ahmedabad', 'Kolkata',
    'Pune', 'Jaipur', 'Lucknow', 'Kanpur', 'Nagpur', 'Indore', 'Thane',
    'Bhopal', 'Visakhapatnam', 'Pimpri-Chinchwad', 'Patna', 'Vadodara',
    'Ghaziabad', 'Ludhiana', 'Agra', 'Nashik', 'Faridabad', 'Meerut',
    'Rajkot', 'Varanasi', 'Srinagar', 'Aurangabad', 'Dhanbad', 'Amritsar',
    'Allahabad', 'Ranchi', 'Howrah', 'Guwahati', 'Chandigarh', 'Mysore',
    'Kochi', 'Thiruvananthapuram', 'Kozhikode', 'Thrissur',
]

def get_city_choices():
    tn = [('', '-- Select City --')]
    tn += [(c, f'TN - {c}') for c in sorted(TAMIL_NADU_CITIES)]
    india = [(c, f'India - {c}') for c in sorted(INDIA_CITIES)]
    return tn + india + [('Others', 'Others')]

def get_year_choices():
    current_year = datetime.date.today().year
    years = [(str(y), str(y)) for y in range(2000, current_year + 2)]
    return [('', '-- Select Year --')] + years


# ── Registration: no city (user fills it in profile update) ──────────────────
class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}))
    batch = forms.ChoiceField(choices=get_year_choices, widget=forms.Select(attrs={'class': 'form-control'}))
    class Meta:
        model = CustomUser
        fields = ['full_name', 'email', 'mobile', 'batch', 'institute']
        widgets = {
            'full_name':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'email':      forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'mobile':     forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mobile Number'}),
            'institute':  forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        BLOCKED_DOMAINS = [
            'mailinator.com', 'guerrillamail.com', 'tempmail.com', 'throwam.com',
            'yopmail.com', 'sharklasers.com', 'guerrillamailblock.com', 'grr.la',
            'spam4.me', 'trashmail.com', 'fakeinbox.com', 'maildrop.cc',
            'dispostable.com', 'mailnull.com', 'spamgourmet.com', 'spamgourmet.net',
            'discard.email', 'spamspot.com', '10minutemail.com', 'tempinbox.com',
        ]
        domain = email.split('@')[-1] if '@' in email else ''
        if domain in BLOCKED_DOMAINS:
            raise forms.ValidationError("Please use a valid, real email address (disposable emails are not allowed).")
        existing = CustomUser.objects.filter(email=email).first()
        if existing and existing.is_active:
            raise forms.ValidationError("An account with this email already exists. Please log in instead.")
        return email

    def validate_unique(self):
        pass  # handled by clean_email

    def clean(self):
        cleaned_data = super().clean()
        pw  = cleaned_data.get('password')
        cpw = cleaned_data.get('confirm_password')
        if pw and cpw and pw != cpw:
            raise forms.ValidationError("Passwords do not match.")
        batch = cleaned_data.get('batch')
        if batch:
            cleaned_data['batch'] = int(batch)
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.batch = self.cleaned_data.get('batch')
        if commit:
            user.save()
        return user


class OTPVerifyForm(forms.Form):
    code = forms.CharField(
        max_length=6, min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control otp-input',
            'placeholder': '••••••',
            'autocomplete': 'one-time-code',
            'inputmode': 'numeric',
            'pattern': '[0-9]{6}',
            'autofocus': 'autofocus',
        })
    )

    def clean_code(self):
        code = self.cleaned_data.get('code', '').strip()
        if not code.isdigit():
            raise forms.ValidationError("Enter the 6-digit code sent to your email.")
        return code


class UserLoginForm(AuthenticationForm):
    username = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your registered email',
            'autofocus': 'autofocus',
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        return email


class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'New Password',
            'autofocus': 'autofocus',
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm New Password',
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        pw = cleaned_data.get('new_password')
        cpw = cleaned_data.get('confirm_password')
        if pw and cpw and pw != cpw:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data


class AdminLoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username', 'autofocus': 'autofocus'}))
    code = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Access Code'}))


# ── Profile update: all professional fields required ─────────────────────────
class EditProfileForm(forms.ModelForm):
    new_password         = forms.CharField(required=False, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New Password (leave blank to keep)'}))
    confirm_new_password = forms.CharField(required=False, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm New Password'}))
    city                 = forms.ChoiceField(choices=get_city_choices, widget=forms.Select(attrs={'class': 'form-control', 'id': 'citySelectEdit'}))
    city_other           = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your city', 'id': 'cityOtherEdit', 'style': 'display:none'}))
    batch                = forms.ChoiceField(choices=get_year_choices, widget=forms.Select(attrs={'class': 'form-control'}))
    class Meta:
        model  = CustomUser
        fields = ['full_name', 'email', 'mobile', 'batch', 'institute',
                  'employment_status', 'current_company', 'designation', 'domain', 'city',
                  'experience_years', 'salary', 'skills', 'resume']
        widgets = {
            'full_name':         forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'email':             forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'mobile':            forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mobile Number'}),
            'institute':         forms.Select(attrs={'class': 'form-control'}),
            'employment_status': forms.Select(attrs={'class': 'form-control', 'id': 'id_employment_status'}),
            'current_company':   forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Infosys, TCS, Zoho', 'id': 'id_current_company'}),
            'designation':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Software Engineer'}),
            'domain':            forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Web Development, Data Science'}),
            'experience_years':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2.5'}),
            'salary':            forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 10 LPA or 40000'}),
            'skills':            forms.HiddenInput(),  # handled by tag UI in template
            'resume':            forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employment_status'].required = True
        self.fields['designation'].required = True
        self.fields['domain'].required = True
        self.fields['experience_years'].required = True
        self.fields['city'].required = False
        status = (self.data.get('employment_status') if self.data else '') or self.initial.get('employment_status') or (self.instance.employment_status if self.instance else '')
        if status != 'Currently Working':
            self.fields['current_company'].required = False
        if status == 'Fresher':
            self.fields['designation'].required = False
            self.fields['experience_years'].required = False
            self.fields['salary'].required = False

    def clean(self):
        cleaned_data = super().clean()
        pw  = cleaned_data.get('new_password')
        cpw = cleaned_data.get('confirm_new_password')
        if pw and pw != cpw:
            raise forms.ValidationError("Passwords do not match.")
        city       = cleaned_data.get('city')
        city_other = cleaned_data.get('city_other')
        if city == 'Others' and not city_other:
            raise forms.ValidationError("Please enter your current city.")
        if city == 'Others':
            cleaned_data['city'] = city_other
        status = cleaned_data.get('employment_status')
        if status == 'Currently Working':
            if not cleaned_data.get('current_company', '').strip():
                raise forms.ValidationError("Please enter your current company name.")
        else:
            cleaned_data['current_company'] = ''


        salary = cleaned_data.get('salary', '').strip()
        if salary:
            import re
            num = re.sub(r'[^0-9.]', '', salary).rstrip('.')
            if num and re.match(r'^\d+(\.\d+)?$', num):
                if float(num) <= 100:
                    cleaned_data['salary'] = num + ' LPA'
                else:
                    cleaned_data['salary'] = '₹' + num
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        new_pw = self.cleaned_data.get('new_password')
        if new_pw:
            user.set_password(new_pw)
        city = self.cleaned_data.get('city')
        user.city = self.cleaned_data.get('city_other', '') if city == 'Others' else city
        batch = self.cleaned_data.get('batch')
        if batch:
            user.batch = int(batch)
        if commit:
            user.save()
        return user
