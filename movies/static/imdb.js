function setupImdb(){
	var $dialog=null, $dialogBody, $wait, $path, $hiddenPath, $form, $error, $select, imdbUrl;
	var imdbFullUrl;
	var mediainfo, imdbCache={};

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
		if (!showUrlMovieInfo($(this).val())){
			showStep(5);
			innerPost(imdbFullUrl, $form.serializeArray(), handleError, function(response){
				updateMovieInfo(response.movie_info);
			});
		}
		return false;
	}

	function updateMovieInfo(info){
		if (info){
			imdbCache[info.url]=info;
			showUrlMovieInfo(info.url);
		} else {
			invalidResponse();
		}		
	}

	function showUrlMovieInfo(url){
		var info = imdbCache[url];
		if (info){
			var src=info.imageLink || '/static/noposter.jpg';
			$('img.step6', $dialogBody).attr('src', src).parent().attr('href',info.url);
			var html=info.actors+'<br>'+info.genres+'<br>'+info.year;
			$('.imdb_info', $dialogBody).html(html);
			showStep(6);
			return true;
		}
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
				$select.html(html);
				showStep(4);
				updateMovieInfo(response.first_movie_info);
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
			$dialog=$('#imdb_dialog').on('shown', handleFileStep1_LoadMediaInfo);
			$dialogBody=$('.modal-body', $dialog);
			$form=$('form', $dialogBody);
			$wait=$('.progress', $dialogBody);
			$path=$('.path', $dialogBody);
			$error=$('.error', $dialogBody);
			$hiddenPath=$('input[name="file.path"]', $dialogBody);
			$select = $('select[name="movie.imdb"]').change(handleFileStep5_LoadImdbInfo);
			imdbUrl=$('a#location-sync-accept-title', $dialogBody).click(handleFileStep3_LoadImdbInfo)[0].href;
			imdbFullUrl=$select.attr('data-href');
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