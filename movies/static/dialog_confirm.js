var DialogConfirm = new function(){
	var $dialog=null, $dialogBody;
	var confirmSettings;

	this.show=function(message, postSettings){
		if (! $dialog) {
			$dialog=$('#dialog_confirm');			
			$dialogBody=$('.modal-body', $dialog);
			confirmSettings = setupAjaxModal($dialog);
			$dialog.on('shown.bs.modal', function(){confirmSettings.submit.focus();});
		}
		confirmSettings.settings = postSettings;
		$dialogBody.text(message);
		$dialog.modal('show');
	}

	this.hide=function(){
		if ($dialog.length) $dialog.modal('hide');	
	}
};