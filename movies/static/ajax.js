function _luajax(settings){
	//success, error, url, data, msg, type
	var msg = null, serror=settings.error, sok=settings.success;
	settings.error = function(){
		var problem = (arguments.length==1) && arguments[0]; 
		if (msg) {
			var reason = settings.message+" failed";
			if (problem) reason+=': '+problem;
			msg.update({type: 'error', message: reason});
		}
		if (serror) serror(problem, msg);
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
			showCloseButton: true
		});
	}
	$.ajax(settings);
}

function ajaxPost(settings) {
	_luajax($.extend({type: 'POST'}, settings));
}

function ajaxPostForm(form, settings) {
	var data = $.extend({url: form.attr('action'), type: 'POST'}, settings);
	data.data = form.serializeArray();
    _luajax(data);
}

function addProgressToModal($modal){
	setupAjaxModal($modal);
}

function setupAjaxModal($modal, settings){
	//Just adds a progress bar that will be automatically shown instead of the submit progress button
	var submit = $("button[type='submit']", $modal);
	if (submit.length) {
		var $parent = submit.parent();
		var $progress=$('.progress', $parent);
		var $error=$('.error_dialog', $parent);
		var oldErrorHandler = settings && settings.error;
		var extSettings = settings && $.extend(settings, {error: showError});

		function reset(){
			submit.show();
			if ($progress.length) $progress.hide();
			if ($error.length) $error.hide();
		}

		function showProgress(){
			submit.hide();
			if ($error.length) $error.hide();
			if (! $progress.length) $progress=$('<div class="progress progress-striped active"><div class="bar" style="width: 100%;"></div></div>').appendTo($parent);
			$progress.show();
		}

		function showError(error){
			submit.show();
			if ($progress.length) $progress.hide();
			if (! $error.length) $error=$('<div class="error_dialog"></div>').appendTo($parent);
			$error.text(error || 'Error accessing server').show();
			if (oldErrorHandler) oldErrorHandler(error);
		}
		$modal.on('hidden', reset);

		submit.click(function(){
			showProgress();
			if (settings==null) return true;
			ajaxPostForm($('form', $modal), extSettings);
			return false;
		});
		$(window).unload(reset);
	}
}
