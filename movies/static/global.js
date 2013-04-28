function iconWhiteCheck(){
	var bg = $('body').css("backgroundColor");
	if (bg){
		var add, remove;		
		if (parseInt(bg.slice(4), 10)>127){
			add='icon-black';
			remove='icon-white';
		} else{
			remove='icon-black';
			add='icon-white';
		}
		$('.'+remove).removeClass(remove).addClass(add);
	}
}

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

$(function() {
	if ($('#locations').length) setupLocations();
	if ($('#locations_sync').length) setupLocationsSync();
	if ($('#movies_control').length) setupMoviesControl();
	iconWhiteCheck();
})