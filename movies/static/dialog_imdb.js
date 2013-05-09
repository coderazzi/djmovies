var DialogImdb = new function(){
	var $dialog=null, $dialogBody, $form, $wait, $path, $hiddenPath, $error;
	var $select, $title, $img, $movieInfo;
	var urlSearchTitle, urlGetImdb;
	var mediainfo, imdbCache={};

	var STEP_1_SERVER_MEDIAINFO=1;
	var STEP_2_EXPECT_TITLE=2;
	var STEP_3_SERVER_TITLE_INFO=3;
	var STEP_4_EXPECT_SELECTION=4;
	var STEP_5_SERVER_MOVIE_INFO=5;
	var STEP_6_EXPECT_CONFIRMATION=6;

	var shownDialogCallback, callbackData;

	this.show=function(filepath, movieId, title, dialogCallback){
		shownDialogCallback = dialogCallback;
		if (! $dialog) {
			$dialog=$('#dialog_imdb');
			$dialogBody=$('.modal-body', $dialog);
			$form=$('form', $dialogBody);
			$wait=$('.progress', $dialogBody);
			$path=$('.path', $dialogBody);
			$hiddenPath=$('input[name="file.path"]', $dialogBody);
			$error=$('.error_dialog', $dialogBody);
			$title=$('input[name="movie.title"]', $dialogBody);	
			$select = $('select[name="movie.imdb"]').change(loadImdbInfoCallback);

			$img=$('img.step6', $dialogBody);
			$movieInfo=$('.imdb_info', $dialogBody);

			urlSearchTitle=$('a#imdb_search_title', $dialogBody).click(searchTitleCallback)[0].href;
			urlGetImdb=$select.attr('data-href');

			$form.keypress(function(e) {
		    	if(e.which == 13) { 
		        	e.preventDefault();
					if ($title.is(":focus")) searchTitleCallback();
		    	}
			});

			callbackData = {
				location: $('input[name="location.id"]', $dialogBody).val(),
				dirpath: $('input[name="location.path"]', $dialogBody).val()
			};

			$('#location-sync-check-title', $dialogBody).click(function(){
				$dialog.modal('hide');
				callbackData.mediainfo=mediainfo;
				callbackData.imdbinfo=imdbCache[$select.val()];
				shownDialogCallback(callbackData);
				return false;
			});
		}
		$path.text(filepath);
		$hiddenPath.val(filepath);
		callbackData.movieId = movieId;
		callbackData.filepath=filepath;

		showStep(STEP_1_SERVER_MEDIAINFO);

		var callback=requestMediaInfo;
		if (title){
			$title.val(title);
			mediainfo=null;
			callback = titleLoadedCallback;
		}
		$dialog.off('shown').on('shown', callback).modal('show');
	}

	function invalidResponse(){handleError('Server error: invalid response');}
	function handleError(error){ $wait.hide(); $error.text(error || 'Error accessing server').show(); }
	function showStep(step){
		$error.hide();
		for (var i=6; i>1; i--)
			if (i==step) $('.step'+i, $dialogBody).show();
			else if (i>step) $('.step'+i, $dialogBody).hide();				
		
		if (step%2){
			$wait.show();
		} else {
			$wait.hide();
			if (step==STEP_2_EXPECT_TITLE) $title.focus();
			else if (step==STEP_4_EXPECT_SELECTION) $select.focus();
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
			$img.attr('src', src).parent().attr('href','http://www.imdb.com'+info.url);
			$movieInfo.html(html);
			showStep(STEP_6_EXPECT_CONFIRMATION);
			return true;
		}
		return false;
	}

	function loadImdbInfoCallback(){
		if (!showUrlMovieInfo($(this).val())){
			showStep(STEP_5_SERVER_MOVIE_INFO);
			ajaxPostForm($form, {
				url: urlGetImdb,
				error: handleError,
				success: function(response){updateMovieInfo(response.movie_info);}
			});
		}
		return false;
	}

	function searchTitleCallback(){
		showStep(STEP_3_SERVER_TITLE_INFO);

		ajaxPostForm($form, {
			url: urlSearchTitle,
			error: handleError, 
			success: function(response){
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
					showStep(STEP_4_EXPECT_SELECTION);
					updateMovieInfo(response.first_movie_info);
				}
			}
		});
		return false;
	}

	function titleLoadedCallback(){		
		showStep(STEP_2_EXPECT_TITLE);
	}

	function requestMediaInfo(){		
		ajaxPostForm($form, {
			error: handleError,
			success: function(response){
				mediainfo = response.mediainfo;
				if (!mediainfo){
					invalidResponse();
				} else {
					$title.val(mediainfo.name);
					titleLoadedCallback();
				}
			}
		});
	}
}