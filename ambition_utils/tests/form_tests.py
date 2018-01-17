from django import forms
from django.core.exceptions import ValidationError
from django.test import TestCase

from ambition_utils.forms import NestedFormMixin, NestedFormMixinBase


class NestedForm1(NestedFormMixin, forms.Form):
    three = forms.CharField(error_messages={
        'required': 'Three is required'
    })
    four = forms.CharField(required=False)

    def save(self, **kwargs):
        return kwargs['number'] * 10


class NestedForm2(NestedFormMixin, forms.Form):
    five = forms.CharField(error_messages={
        'required': 'Five is required'
    })
    six = forms.CharField(required=False)

    def save(self, **kwargs):
        return 2


class OptionalForm(NestedFormMixin, forms.Form):
    seven = forms.CharField(error_messages={
        'required': 'seven is required'
    })
    eight = forms.CharField(required=False)

    def save(self, **kwargs):
        return 'optional value'


class ParentForm(NestedFormMixin, forms.Form):
    nested_form_configs = [{
        'class': NestedForm1,
        'key': 'nested_form_1',
        'required': False,
        'required_key': 'nested_form_1_required',
        'pre': True,
    }, {
        'class': NestedForm2,
        'key': 'nested_form_2',
        'required': False,
        'required_key': 'nested_form_2_required',
        'pre': True,
    }, {
        'class': OptionalForm,
        'key': 'optional',
        'required': False,
        'field_prefix': 'optional_1',
        'required_key': 'optional_required',
        'pre': True,
    }, {
        'class': OptionalForm,
        'key': 'optional_2',
        'field_prefix': 'optional_2',
        'required_key': 'optional_required_2',
        'required': False,
        'post': True,
    }]

    one = forms.CharField(error_messages={
        'required': 'One is required'
    })
    two = forms.CharField(required=False)

    # Flags for the 3 nested forms
    nested_form_1_required = forms.BooleanField(required=False)
    nested_form_2_required = forms.BooleanField(required=False)
    optional_required = forms.BooleanField(required=False)
    optional_required_2 = forms.BooleanField(required=False)

    def get_pre_save_method_kwargs(self):
        return {
            'number': 10,
            'another_number': 'ten'
        }

    def save_form(self, **kwargs):
        return 'the object'


class FormWithAlwaysRequired(NestedFormMixin, forms.Form):
    nested_form_configs = [{
        'class': NestedForm1,
        'key': 'nested_form_1',
        'required': True,
        'pre': True,
    }, {
        'class': NestedForm2,
        'key': 'nested_form_2',
        'required': True,
        'pre': True,
    }, {
        'class': OptionalForm,
        'key': 'optional',
        'required': True,
        'pre': True,
    }]

    one = forms.CharField(error_messages={
        'required': 'One is required'
    })
    two = forms.CharField(required=False)

    # Flags for the 3 nested forms
    nested_form_1_required = forms.BooleanField(required=False)
    nested_form_2_required = forms.BooleanField(required=False)
    optional_required = forms.BooleanField(required=False)


class FormWithOptional(NestedFormMixin, forms.Form):
    nested_form_configs = [{
        'class': NestedForm1,
        'key': 'nested_form_1',
        'required': False,
        'required_key': 'nested_form_1_required',
        'pre': True,
    }, {
        'class': OptionalForm,
        'key': 'optional',
        'required': False,
        'required_key': 'optional_required',
        'pre': True,
    }]

    one = forms.CharField(error_messages={
        'required': 'One is required'
    })
    two = forms.CharField(required=False)

    # Flags for the 2 nested forms
    nested_form_1_required = forms.BooleanField(required=False)
    optional_required = forms.BooleanField(required=False)


class NestedFormMixinBaseTest(TestCase):

    def test_get_pre_save_method_kwargs(self):
        """
        Checks return value of pre save method
        """
        mixin = NestedFormMixinBase()

        self.assertEqual(mixin.get_pre_save_method_kwargs(), {})

    def test_get_post_save_method_kwargs(self):
        """
        Checks return value of post save method
        """
        mixin = NestedFormMixinBase()

        self.assertEqual(mixin.get_post_save_method_kwargs(one='two'), {'one': 'two'})

    def test_save_form(self):
        """
        Checks return value of save form method
        """
        mixin = NestedFormMixinBase()

        self.assertEqual(mixin.save_form(), None)

    def test_save(self):
        """
        Makes sure parent form save is called
        """
        class ParentForm(forms.Form):

            def save(self):
                return 'saved'


        class ChildForm(NestedFormMixinBase, ParentForm):
            pass


        form = ChildForm()

        self.assertEqual(form.save(), 'saved')


class NestedFormMixinTest(TestCase):

    def test_field_prefix_validation_error(self):
        """
        Makes sure a validation error is raised if two of the same form exist but both don't have a field prefix
        """
        class Form1(forms.Form):
            pass

        class ParentForm1(NestedFormMixin, forms.Form):
            nested_form_configs = [{
                'class': Form1,
            }, {
                'class': Form1,
            }]

        with self.assertRaises(ValidationError):
            ParentForm1()

    def test_nested_required_fields(self):
        """
        The ParentForm required field and 2 of the nested forms' required fields should be required. The second
        optional form has a field prefix and provides the required field, so it should not cause an additional
        validation error.
        """
        data = {
            'nested_form_1_required': '1',
            'nested_form_2_required': '1',
            'optional_required_2': '1',
            'optional_2_seven': 'good'
        }

        form = ParentForm(data=data)
        self.assertFalse(form.is_valid())

        self.assertEqual(len(form.errors), 3)

    def test_optional_form_flag_false(self):
        """
        Verifies an optional form is not required when its flag is false
        """
        data = {
            'nested_form_1_required': '1',
            'optional_required': 'False'
        }

        form = FormWithOptional(data=data)
        self.assertFalse(form.is_valid())

        self.assertEqual(len(form.errors), 2)

    def test_optional_form_flag_missing(self):
        """
        Verifies an optional form is not required when its flag is missing
        """
        data = {
            'nested_form_1_required': '1',
        }

        form = FormWithOptional(data=data)
        self.assertFalse(form.is_valid())

        self.assertEqual(len(form.errors), 2)

    def test_optional_form_flag_true(self):
        """
        Verifies an optional form is required when its flag is true
        """
        data = {
            'nested_form_1_required': 'True',
            'optional_required': 'True'
        }

        form = FormWithOptional(data=data)
        self.assertFalse(form.is_valid())

        self.assertEqual(len(form.errors), 3)

    def test_full_scenario(self):
        """
        Covers all presave, save, postsave scenarios with multiple forms
        """
        data = {
            'nested_form_1_required': '1',
            'nested_form_2_required': '1',
            'optional_required_2': '1',
            'one': '1',
            'three': '3',
            'five': '5',
            'seven': '7',
        }

        form = ParentForm(data=data)

        self.assertTrue(form.is_valid())

        return_value = form.save()

        self.assertEqual(return_value, 'the object')
