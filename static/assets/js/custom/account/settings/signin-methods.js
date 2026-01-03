"use strict";


var KTAccountSettingsSigninMethods = function () {
    var passwordMainEl;
    var passwordEditEl;
    var passwordChange;
    var passwordCancel;
    var passwordForm;

    var toggleChangePassword = function () {
        passwordMainEl.classList.toggle('d-none');
        passwordChange.classList.toggle('d-none');
        passwordEditEl.classList.toggle('d-none');
    }

    var initSettings = function () {
        passwordChange.querySelector('button').addEventListener('click', function () {
            toggleChangePassword();
        });

        passwordCancel.addEventListener('click', function () {
            toggleChangePassword();
        });
    }

    var sendChangePasswordForm = function () {
        var passwordChangeForm = $("#kt_signin_change_password");

        var action = passwordChangeForm.attr('action');
        var csrfToken = passwordChangeForm.find('input[name="csrfmiddlewaretoken"]').val();

        $.ajax({
            url: action,
            type: 'POST',
            data: passwordChangeForm.serialize(),
            headers: {
                'X-CSRFToken': csrfToken
            },
            success: function(response) {
                swal.fire({
                    text: "Password changed successfully.",
                    icon: "success",
                    buttonsStyling: false,
                    confirmButtonText: "Ok, got it!",
                    customClass: {
                        confirmButton: "btn btn-primary"
                    }
                });
            },
            error: function(xhr, errmsg, err) {
                showErrorMessage();
            }
        });
    }

    var showErrorMessage = function () {
        swal.fire({
            text: "Sorry, looks like there are some errors detected, please try again.",
            icon: "error",
            buttonsStyling: false,
            confirmButtonText: "Ok, got it!",
            customClass: {
                confirmButton: "btn btn-primary"
            }
        });
    }

    var handleChangePassword = function (e) {
        var validation;

        if (!passwordForm) {
            return;
        }

        validation = FormValidation.formValidation(
            passwordForm,
            {
                fields: {
                    old_password: {
                        validators: {
                            notEmpty: {
                                message: 'Current Password is required'
                            }
                        }
                    },

                    new_password1: {
                        validators: {
                            notEmpty: {
                                message: 'New Password is required'
                            },
                            different: {
                                compare: function() {
                                    return passwordForm.querySelector('[name="old_password"]').value;
                                },
                                message: 'The new password is the same as the current password'
                            },
                        }
                    },

                    new_password2: {
                        validators: {
                            notEmpty: {
                                message: 'Confirm Password is required'
                            },
                            identical: {
                                compare: function() {
                                    return passwordForm.querySelector('[name="new_password1"]').value;
                                },
                                message: 'The password and its confirm are not the same'
                            }
                        }
                    },
                },

                plugins: { //Learn more: https://formvalidation.io/guide/plugins
                    trigger: new FormValidation.plugins.Trigger(),
                    bootstrap: new FormValidation.plugins.Bootstrap5({
                        rowSelector: '.fv-row'
                    })
                }
            }
        );

        passwordForm.querySelector('#kt_password_submit').addEventListener('click', function (e) {
            e.preventDefault();

            validation.validate().then(function (status) {
                if (status == 'Valid') {
                    swal.fire({
                        text: "Sent password reset email?",
                        icon: "info",
                        buttonsStyling: false,
                        confirmButtonText: "Ok, got it!",
                        customClass: {
                            confirmButton: "btn font-weight-bold btn-light-primary"
                        }
                    }).then(function(){
                        sendChangePasswordForm();
                        passwordForm.reset();
                        validation.resetForm();
                        toggleChangePassword();
                    });
                } else {
                    showErrorMessage();
                }
            });
        });
    }

    return {
        init: function () {
            passwordMainEl = document.getElementById('kt_signin_password');
            passwordEditEl = document.getElementById('kt_signin_password_edit');
            passwordChange = document.getElementById('kt_signin_password_button');
            passwordCancel = document.getElementById('kt_password_cancel');
            passwordForm = document.getElementById('kt_signin_change_password');

            initSettings();
            handleChangePassword();
        }
    }
}();

KTUtil.onDOMContentLoaded(function() {
    KTAccountSettingsSigninMethods.init();
});
