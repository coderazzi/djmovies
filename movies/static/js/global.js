var MAIN_UQUERY_URL='/uquery'
var BASE_UQUERY_URL=MAIN_UQUERY_URL+'/query'
var UQUERY_URL=BASE_UQUERY_URL+'/'

var csrftoken = $.cookie('csrftoken');

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

$.ajaxSetup({
    crossDomain: false, // obviates need for sameOrigin test
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type)) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

Messenger.options = {
	extraClasses: 'messenger-fixed messenger-on-bottom messenger-on-right',
	theme: 'future'
}

// Common method to show a connection error
function alert_server_error(){
    setTimeout(function(){
        swal({   
            title: "Error accessing server",   
            type: "error",   
            confirmButtonClass: "btn-danger",
        });
    },500);
}


$(function() {
    function setupIf(selector, setupFunction){
        var $selector=$(selector);
        if ($selector.length) setupFunction($selector);
    }

    $('.ic_tooltip_img').tooltip({html: true, placement:'right', title:function(){
        return '<img src="'+$(this).attr('src')+'">';
    }});

    setupIf('#locations-list', setupLocations);
    setupIf('#locations_sync', setupLocationsSync);
    setupIf('#movies_control', setupMoviesControl);
    setupIf('#subtitles-handling-form', setupSubtitlesHandling);
    setupIf('#index_html', setupIndex);
    setupIf('#imdb_search', setupImdbSearch);
    setupIf('#uquery-list', setupUquery);
    setupIf('#uquery-results', setupUqueryResults);
})