/**CUFON SCRIPT**/
$(document).ready(function () {
    Cufon.replace('h1, h2, .large_button');
});
/**END CUFON SCRIPT**/

/**TINY SLIDER SCRIPT**/
$(document).ready(function () {
    $('#tiny-slider').tinycarousel({
        start: 1, // where should the carousel start?
        display: 1, // how many blocks do you want to move at a time?
        axis: 'x', // vertical or horizontal scroller? 'x' or 'y' .
        controls: true, // show left and right navigation buttons?
        pager: false, // is there a page number navigation present?
        interval: 1000, // move to the next block on interval.
        intervaltime: 3000, // interval time in milliseconds.
        rewind: true, // If interval is true and rewind is true it will play in reverse if the last slide is reached
        animation: true, // false is instant, true is animate.
        duration: 800, // how fast must the animation move in milliseconds?
        callback: null // function that executes after every move
    });
});
/**END TINY SLIDER SCRIPT**/

/**TIPSY SCRIPT**/
$(document).ready(function () {
    $('#featured, .twitter_icon, .facebook_icon, .flickr_icon, .rss_icon').tipsy({fade: true, gravity: 's'});
});
/**END TIPSY SCRIPT**/

/**TOGGLE SCRIPT**/
$(document).ready(function () {
    $(".toggle_container").hide();
    $(".trigger").click(function () {
        $(this).toggleClass("active").next().slideToggle("slow");
    });

});
/**END TOGGLE SCRIPT**/

/**IMAGE SPOTLIGHT**/
$(document).ready(function () {
    $(".screens li").fadeTo("slow", 0.7); // The value 0.7 sets the opacity of the thumbs to fade down to 60% when the page loads

    $(".screens li").hover(function () {
        $(this).fadeTo("fast", 1.0); // The value 1.0 should set the opacity to 100% on hover
    }, function () {
        $(this).fadeTo("fast", 0.7); // The value 0.7 should set the opacity back to 60% on mouseout
    });
});
/**END IMAGE SPOTLIGHT**/

/** CONTACT FORM CODE **/
$(document).ready(function () {
    $("#ajax-contact-form").submit(function () {

        /** 'this' refers to the current submitted form**/
        var str = $(this).serialize();

        $.ajax({
            type: "POST",
            url: "contact.php",
            data: str,
            success: function (msg) {

                $("#note").ajaxComplete(function (event, request, settings) {

                    if (msg == 'OK') /** Message Sent? Show the 'Thank You' message and hide the form**/
                    {
                        result = '<div class="notification_ok">Your message has been sent. Thank you!<\/div>';
                        $("#ajax-contact-form").hide();
                    }
                    else {
                        result = msg;
                    }

                    $(this).html(result);

                });

            }

        });

        return false;

    });

});
/** END CONTACT FORM CODE **/