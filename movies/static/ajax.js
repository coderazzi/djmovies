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

function alertError(error){
	Messenger().post({
			message:error,
			type: 'error',
			showCloseButton: true
		});
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
	setupAjaxModal($modal, null);
}

function setupAjaxModal($modal, settings){
	var submit = $("button[type='submit']", $modal);
	if (!submit.length) {
		submit = $(".modal-footer a.btn-primary", $modal);
		if (!submit.length) return;
	}
	var $parent = submit.parent();
	var $progress=$('.progress', $parent);
	var $error=$('.error_dialog', $parent);
	if (settings===undefined) settings={};
	var superSettings={
		settings: settings, 
		submit:submit,
		showError: showError,
		hideProgress: hideProgress
	};

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

	function hideProgress(){
		if ($progress.length) $progress.hide();
		submit.show();
	}

	function showError(error){
		submit.show();
		if ($progress.length) $progress.hide();
		if (! $error.length) $error=$('<div class="error_dialog"></div>').appendTo($parent);
		$error.text(error || 'Error accessing server').show();
	}
	$modal.on('hidden', reset);

	submit.click(function(){
		showProgress();
		var settings = superSettings.settings;
		if (settings==null) return true;
		var extSettings = settings && $.extend(settings, {error: showError});
		var $form = $('form', $modal);
		if ($form.length){
			ajaxPostForm($form, extSettings);
		} else {
			ajaxPost(extSettings);
		}
		return false;
	});
	$(window).unload(reset);
	return superSettings;
}
