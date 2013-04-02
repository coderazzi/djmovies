function innerPost(where, what, failFunction, getFunction) {
    $.post(where, what, function (response, status, xhr) {
        if (status === "error") {
            failFunction();
        } else {
        	var error = response.error;
        	if (error){
            	failFunction(error);
        	} else {
	            getFunction(response);
	        }
        } 
    }).error(function (xhr, status, error) { failFunction();});
}

function postForm(form, failFunction, getFunction, where) {
    innerPost(where || form.attr('action'), form.serializeArray(), failFunction, getFunction);
}


function prepareWaitOnPostForm(form, showWait){
	//Just adds a progress bar that will be automatically shown instead of the submit progress button
	var submit = $("button[type='submit']", form);
	if (submit.length) {
		var parent = submit.parent();
		var progress=$('.progress', parent);
		if (showWait){
			submit.hide();
			if (progress.length){
				progress.show();
			} else {
				progress=$('<div class="progress progress-striped active"><div class="bar" style="width: 100%;"></div></div>').appendTo(parent);								
			}
		} else {
			submit.show();
			if (progress.length){
				progress.hide();
			} else {
				submit.click(function(){
					prepareWaitOnPostForm(form, true);
					return true;
				});
				$(window).unload(function(){
					//in case the user comes back to this page doing history back, 
					prepareWaitOnPostForm(form, false);
				});
			}
		}
	}
}

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


$(function() {
	if ($('#locations').length) setupLocations();
	if ($('#locations_sync').length) setupLocationsSync();
	iconWhiteCheck();
})