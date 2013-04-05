function luajax(settings){
	//success, error, url, data, msg, type
	var msg = null, serror=settings.error, sok=settings.success;
	settings.error = function(){
		if (msg) msg.update({type: 'error', message: settings.msg+" failed"});
		if (arguments.length==1) serror(response.error, msg); 
		else serror(null, msg); 			
	}
	settings.success=function(response){
    	if (response && response.error) {
    		settings.error(response.error);
    	} else {
    		if (msg) msg.update({type: 'success', message: settings.msg + " done"});
    		sok(response, msg);
    	}
	};
	if (settings.data){
		if (!(settings.data instanceof Array)){
			settings.datatype='json';
			settings.contentType='application/json';
		}
	}
	if (settings.msg){
		msg = Messenger().post({
			message:settings.msg,
			type: 'info'
		});
	}
	$.ajax(settings);
}

function ajaxPost(settings) {
    // $.post(where, what, function (response, status, xhr) {
    //     if (status === "error") {
    //         failFunction();
    //     } else {
    //     	var error = response.error;
    //     	if (error){
    //         	failFunction(error);
    //     	} else {
	   //          getFunction(response);
	   //      }
    //     } 
    // }).error(function (xhr, status, error) { failFunction();});
	luajax($.extend({type: 'POST'}, settings));
	// luajax({
	// 	url: settings.url,
	// 	type: 'POST',
	// 	data: settings.data,
	// 	error: settings.error,
	// 	success: settings.success
	// }, messengerMsg);
}

//function ajaxPostForm(form, failFunction, getFunction, where) {
function ajaxPostForm(form, settings) {
	var data = $.extend({url: form.attr('action')}, settings);
	//var info = data.data;
	data.data = form.serializeArray();
    ajaxPost(data);
}


function prepareWaitOnajaxPostForm(form, showWait){
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
					prepareWaitOnajaxPostForm(form, true);
					return true;
				});
				$(window).unload(function(){
					//in case the user comes back to this page doing history back, 
					prepareWaitOnajaxPostForm(form, false);
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