function setupImdb(){
	var $dialog, $dialogBody, $wait, $path, $hiddenPath, $form, $error, $select, $title, $img, $movieInfo;
	var imdbUrl, imdbFullUrl;
	var mediainfo, imdbCache={};

	function invalidResponse(){handleError('Server error: invalid response');}

	function handleError(error){
		$wait.hide();
		$error.text(error || 'Error accessing server').show();
	}

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
			var html=info.actors+'<br>'+info.genres+'<br>'+info.year;
			$img.attr('src', src).parent().attr('href',info.url);
			$movieInfo.html(html);
			showStep(6);
			return true;
		}
		return false;
	}

	function loadImdbInfoCallback(){
		if (!showUrlMovieInfo($(this).val())){
			showStep(5);
			innerPost(imdbFullUrl, $form.serializeArray(), handleError, function(response){
				updateMovieInfo(response.movie_info);
			});
		}
		return false;
	}

	function searchTitleCallback(){
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

	function dialogShownCallback(){
		postForm($form, handleError, function(response){
			mediainfo = response.mediainfo;
			if (!mediainfo){
				invalidResponse();
			} else {
				$title.val(mediainfo.name);
				showStep(2);
			}
		});
	}

	function handleFile(path){
		showStep(1);
		$path.text(path);
		$hiddenPath.val(path);
		$dialog.modal();
	}

	$dialog=$('#imdb_dialog').on('shown', dialogShownCallback);
	$dialogBody=$('.modal-body', $dialog);
	$form=$('form', $dialogBody);
	$wait=$('.progress', $dialogBody);
	$path=$('.path', $dialogBody);
	$error=$('.error', $dialogBody);
	$hiddenPath=$('input[name="file.path"]', $dialogBody);
	$title=$('input[name="movie.title"]', $dialogBody);	
	$select = $('select[name="movie.imdb"]').change(loadImdbInfoCallback);

	$img=$('img.step6', $dialogBody);
	$movieInfo=$('.imdb_info', $dialogBody);

	imdbUrl=$('a#imdb_search_title', $dialogBody).click(searchTitleCallback)[0].href;
	imdbFullUrl=$select.attr('data-href');

	$('.search_path').click(function(){
		var path = $('.path', $(this).parent().parent());
		if (path.length){
			handleFile(path.text());
		} 
		return false;
	});

}