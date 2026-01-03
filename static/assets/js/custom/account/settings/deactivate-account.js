"use strict";


var KTAccountSettingsDeactivateAccount = function () {
    var form;
    var validation;
    var submitButton;

    var initValidation = function () {
        validation = FormValidation.formValidation(
            form,
            {
                fields: {
                    deactivate: {
                        validators: {
                            notEmpty: {
                                message: 'Please check the box to deactivate your account'
                            }
                        }
                    }
                },
                plugins: {
                    trigger: new FormValidation.plugins.Trigger(),
                    submitButton: new FormValidation.plugins.SubmitButton(),
                    bootstrap: new FormValidation.plugins.Bootstrap5({
                        rowSelector: '.fv-row',
                        eleInvalidClass: '',
                        eleValidClass: ''
                    })
                }
            }
        );
    }

    var sendDeactivateAccountForm = function () {
        var desactiveForm = $("#kt_account_deactivate_form");

        var action = desactiveForm.attr('action');
        var csrfToken = desactiveForm.find('input[name="csrfmiddlewaretoken"]').val();

        $.ajax({
            url: action,
            type: 'POST',
            data: desactiveForm.serialize(),
            headers: {
                'X-CSRFToken': csrfToken
            },
            success: function(response) {
                swal.fire(
                    'Successfully deactivated your account.',
                    'Your account has been deactivated.',
                    'success'
                ).then(() => {
                    location.reload();
                });
            },
            error: function(xhr, errmsg, err) {
                Swal.fire({
                    text: 'Error!',
                    icon: 'error',
                    buttonsStyling: false,
                    confirmButtonText: 'Ok, got it!',
                    customClass: {
                        confirmButton: "btn btn-primary"
                    }
                })
            }
        });
    }

    var handleForm = function () {
        submitButton.addEventListener('click', function (e) {
            e.preventDefault();

            validation.validate().then(function (status) {
                if (status == 'Valid') {
                    swal.fire({
                        text: "Are you sure you would like to deactivate your account?",
                        icon: "warning",
                        buttonsStyling: false,
                        showDenyButton: true,
                        confirmButtonText: "Yes",
                        denyButtonText: 'No',
                        customClass: {
                            confirmButton: "btn btn-light-primary",
                            denyButton: "btn btn-danger"
                        }
                    }).then((result) => {
                        if (result.isConfirmed) {
                            sendDeactivateAccountForm();
                        } else if (result.isDenied) {
                            Swal.fire({
                                text: 'Account not deactivated.',
                                icon: 'info',
                                confirmButtonText: "Ok",
                                buttonsStyling: false,
                                customClass: {
                                    confirmButton: "btn btn-light-primary"
                                }
                            })
                        }
                    });
                } else {
                    swal.fire({
                        text: "Sorry, looks like there are some errors detected, please try again.",
                        icon: "error",
                        buttonsStyling: false,
                        confirmButtonText: "Ok, got it!",
                        customClass: {
                            confirmButton: "btn btn-light-primary"
                        }
                    });
                }
            });
        });
    }

    return {
        init: function () {
            form = document.querySelector('#kt_account_deactivate_form');

            if (!form) {
                return;
            }

            submitButton = document.querySelector('#kt_account_deactivate_account_submit');

            initValidation();
            handleForm();
        }
    }
}();

KTUtil.onDOMContentLoaded(function() {
    KTAccountSettingsDeactivateAccount.init();
});
