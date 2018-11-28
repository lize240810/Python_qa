$(function () {

    var paraTag = $('.contact-form #submit').parent('div');

    $(paraTag).children('button').remove();
    $(paraTag).append('<input  class="contact_button button btn btn-primary" type="button" name="submit" id="submit" value="Send Message" />');

    $('.contact-form #submit').click(function () {
        var firstName = $('input#firstName').val();
        var lastName = $('input#lastName').val();
        var phone = $('input#phone').val();
        var message = $('textarea#message').val();
        var subject = $('input#subject').val();
        if (firstName === '') {
            $('[name="firstName"]').addClass('vaidate_error');
        } else {
            $('[name="firstName"]').removeClass('vaidate_error');
        }
        if (lastName === '') {
            $('[name="lastName"]').addClass('vaidate_error');
        } else {
            $('[name="lastName"]').removeClass('vaidate_error');
        }
        if (lastName === '') {
            $('[name="phone"]').addClass('vaidate_error');
        } else {
            $('[name="phone"]').removeClass('vaidate_error');
        }
        if (message === "") {
            $('[name="message"]').addClass('vaidate_error');
        } else {
            $('[name="message"]').removeClass('vaidate_error');
        }
        if (subject === "") {
            $('[name="subject"]').addClass('vaidate_error');
        } else {
            $('[name="subject"]').removeClass('vaidate_error');
        }

        $.ajax({
            type: 'post',
            url: 'sendEmail.php',
            data: 'firstName=' + firstName + "&lastName=" + lastName + '&subject=' + subject + '&message=' + message + "&phone=" + phone,
            success: function (results) {
                $('div#response').html(results).css('display', 'block');

            }
        }); // end ajax
    });

});
		