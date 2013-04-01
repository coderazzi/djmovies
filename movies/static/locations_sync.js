function innerPost(where, what, failFunction, getFunction) {
    $.post(where, what, function (response, status, xhr) {
        if (status === "error") {
            failFunction();
        } else {
        	console.log(response);
        	var error = response.error;
        	console.log(error);
        	if (error){
            	failFunction(error);
        	} else {
	            getFunction(response);
	        }
        } 
    }).error(function (xhr, status, error) { console.log(error);failFunction(status, error);});
};

function postForm(form, failFunction, getFunction, where) {
    innerPost(where || form.attr('action'), form.serializeArray(), failFunction, getFunction);
};





function setupLocationsSync(){
	var $dialog=null, $dialogBody, $wait, $path, $hiddenPath, $form;

	function handleError(step, error){
		$wait.hide();
		$('<div class="ajaxerror step'+(step+1)+'">'+(error || 'Error accessing server')+'</div>').appendTo($dialogBody);
	}

	function invalidResponse(step){handleError(step, 'Server error: invalid response');}

	function handleFileStep1(){
		postForm($form, 
			function(error){handleError(1, error);}, 
			function(response){
				var mediainfo = response.result && response.result.mediainfo;
				if (!mediainfo){
					invalidResponse(1);
				} else {

				}
			}
		);
	}

	function handleFile(path){
		if (!$dialog) {
			$dialog=$('#locations_sync_dialog').on('shown', handleFileStep1);
			$dialogBody=$('.modal-body', $dialog);
			$form=$('form', $dialogBody);
			$wait=$('.progress', $dialogBody);
			$path=$('.path', $dialogBody);
			$hiddenPath=$('input[name="file.path"]', $dialogBody);
		}
		$('.step2', $dialog).remove();		
		$wait.show();
		$path.text(path);
		$hiddenPath.val(path);
		$dialog.modal();
	}

	$('.search_path').click(function(){
		var path = $('.path', $(this).parent().parent());
		if (path.length){
			handleFile(path.text());
		} 
		return false;
	});

}