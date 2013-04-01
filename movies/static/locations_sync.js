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
};

function postForm(form, failFunction, getFunction, where) {
    innerPost(where || form.attr('action'), form.serializeArray(), failFunction, getFunction);
};





function setupLocationsSync(){
	var $dialog=null, $dialogBody, $wait, $path, $hiddenPath, $form, $error, imdbUrl, imdbFullUrl;
	var mediainfo;

	function showStep(step){
		$error.hide();
		for (var i=6; i>1; i--){
			if (i==step){
				$('.step'+i, $dialogBody).show();
			} else if (i>step){
				$('.step'+i, $dialogBody).hide();				
			}
		}
		if (step%2){
			$wait.show();
		} else {
			$wait.hide();
			if (step==2){
				$('a.step2', $dialog).focus();
			} else if (step==4){
				$('select.step4', $dialog).focus();
			}
		}
	}

	function handleError(error){
		$wait.hide();
		$error.text(error || 'Error accessing server').show();
	}

	function invalidResponse(){handleError('Server error: invalid response');}

	function handleFileStep5_LoadImdbInfo(){
		showStep(5);

		// var info = $form.serializeArray();
		// info.push({name: 'mediainfo', value: mediainfo}); //see: http://api.jquery.com/serializeArray/		

		innerPost(imdbFullUrl, $form.serializeArray(), handleError, function(response){
			var info = response.info;
			if (!info){
				invalidResponse();
			} else {
				$('.step6 img', $dialogBody).attr('src', info.imageLink);
				showStep(6);
				// var html='';
				// for (var each in references){
				// 	var reference=references[each];
				// 	html+='<option value="'+reference[0]+'">'+reference[1];
				// 	if (reference[2]) html+=' '+reference[2];
				// 	html+='</a></option>';
				// }
				// $('select[name="movie.imdb"]', $dialogBody).html(html);
				// showStep(4);
			}
		});
		return false;
	}

	function handleFileStep3_LoadImdbInfo(){
		showStep(3);

		innerPost(imdbUrl, $form.serializeArray(), handleError, function(response){
			var references = response.links;
			if (!references){
				invalidResponse();
			} else if (!references.length){
				handleError('No IMDB info for such title. Try changing it');
			} else {
				var html='';
				for (var each in references){
					var reference=references[each];
					html+='<option value="'+reference[0]+'">'+reference[1];
					if (reference[2]) html+=' '+reference[2];
					html+='</a></option>';
				}
				$('select[name="movie.imdb"]', $dialogBody).html(html);
				showStep(4);
			}
		});
		return false;
	}

	function handleFileStep1_LoadMediaInfo(){
		postForm($form, handleError, function(response){
			mediainfo = response.mediainfo;
			if (!mediainfo){
				invalidResponse();
			} else {
				$('input[name="movie.title"]', $dialogBody).val(mediainfo.name);
				showStep(2);
			}
		});
	}

	function handleFile(path){
		if (!$dialog) {
			$dialog=$('#locations_sync_dialog').on('shown', handleFileStep1_LoadMediaInfo);
			$dialogBody=$('.modal-body', $dialog);
			$form=$('form', $dialogBody);
			$wait=$('.progress', $dialogBody);
			$path=$('.path', $dialogBody);
			$error=$('.error', $dialogBody);
			$hiddenPath=$('input[name="file.path"]', $dialogBody);
			imdbUrl=$('a#location-sync-accept-title', $dialogBody).click(handleFileStep3_LoadImdbInfo)[0].href;
			imdbFullUrl=$('a#location-sync-check-title', $dialogBody).click(handleFileStep5_LoadImdbInfo)[0].href;
		}
		showStep(1);
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