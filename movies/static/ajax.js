function luajax(settings){
	//success, error, url, data, msg, type
	var msg = null, serror=settings.error, sok=settings.success;
	settings.error = function(){
		if (msg) msg.update({type: 'error', message: settings.message+" failed"});
		if (serror){
			if (arguments.length==1) serror(arguments[0], msg); 
			else serror(null, msg);
		}
	}
	settings.success=function(response){
    	if (response && response.error) {
    		settings.error(response.error);
    	} else {
    		if (msg) msg.update({type: 'success', message: settings.message + " done"});
    		sok(response, msg);
    	}
	};
	if (settings.data){
		if (!(settings.data instanceof Array)){
			settings.datatype='json';
			settings.contentType='application/json';
			settings.data=JSON.stringify(settings.data);
		}
	}
	if (settings.message){
		msg = Messenger().post({
			message:settings.message,
			type: 'info',
		});
	}
	$.ajax(settings);
}

function ajaxPost(settings) {
	luajax($.extend({type: 'POST'}, settings));
}

function ajaxPostForm(form, settings) {
	var data = $.extend({url: form.attr('action'), type: 'POST'}, settings);
	data.data = form.serializeArray();
    luajax(data);
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
