function setupLocationsSync($locationsSyncSelector){
	var $problemDialog = $('#locations_sync_problems_dialog');

	var $stDialog, $stTitleText, $stPathText, $stPathInput;
	var $stLanguage, $stMovie, $stNormalize;	

	var $fetchDialog, $fetchTitleText;
	var $fetchLanguage, $fetchMovie, $fetchSelection, $fetchDirCreate, $fetchTitle;	

	var $subShowForm, $subShowMovieId, $subShowPath;
	
	var $updatingTr;

	var $ref_add, $ref_remove;

	var locationId, locationPath, fetchingMatches, fetchDialogSettings;
	var urlRemoveSubtitle, urlEditMovie, urlRemoveMovie, urlRefreshInfo, urlCleanSubtitles, urlTrashSubtitle;

	function checkPlusMinusMovies(){
		var plusMovies=$('.create-movie'), minusMovies=$('.remove-movie');
		if (plusMovies.length>0){
			var name = $(plusMovies[0]).attr('name');
			$ref_add.show().attr('href', '#'+name);			
		} else {
			$ref_add.hide();
		}
		if (minusMovies.length>0){
			var name = $(minusMovies[0]).attr('name');
			$ref_remove.show().attr('href', '#'+name);			
		} else {
			$ref_remove.hide();
		}
	}

	function setupEventHandlers(){
		$('.edit-movie').click(editMovieCallback);
		$('.remove-movie').click(removeMovieCallback);
		$('.edit-subtitle').off('click').click(editSubtitleCallback);
		$('.remove-subtitle').off('click').click(removeSubtitleCallback);
		$('.fetch-subtitle').off('click').click(fetchSubtitlesCallback);
		$('.refresh-subtitles').off('click').click(refreshSubtitlesCallback);
		$('.clean-subtitles').off('click').click(cleanSubtitlesCallback);
		$('.trash-subtitle').off('click').click(trashSubtitleCallback);
		$('.shift-subtitle').off('click').click(showSubtitleCallback);
	}

	function updateMovieInfo($tr, html){
		var $next=$tr.next();
		while ($next.length && $next.hasClass('subtitle')){
			var $rem = $next;
			$next = $next.next();
			$rem.remove();
		}
		if (html){
			$tr.replaceWith(html);
			setupEventHandlers();
			movieEdition(getMovieId); //to be checked!
		} else {
			$tr.remove();
		}
		checkPlusMinusMovies();
	}

	function editMovieCallback(){
		$updatingTr=getMainRow($(this)); 
		var path = $('.path', $updatingTr), title=$('.title', $updatingTr);
		if (path.length){
			DialogImdb.show(
				path.text(), 
				$updatingTr.attr('data-movie-id'), 
				title && title.text(),
				function(info){
				ajaxPost({
					url: urlEditMovie,
					message: 'Adding movie information',
					data: info,
					success: function(response){
						updateMovieInfo($updatingTr, response);
					}
				});
			});
		} 
		return false;
	}

	function removeMovieCallback(){
		$updatingTr=getMainRow($(this)); 

		var movieId=$updatingTr.attr('data-movie-id');
		var title=$.trim($updatingTr.find('.title').text())

		DialogConfirm.show('Are you sure to remove from database the movie '+title+'?',
			{
				url:urlRemoveMovie,
				success: function(response){
					updateMovieInfo($updatingTr);
					DialogConfirm.hide();
				},
				message:'Movie deletion',
				data:{
					movieId:movieId,
					locationId: locationId
				}
			});
		return false;
	}

	function showSubtitleCallback(){
		var info = getSubtitleRow($(this));

		if (!$subShowForm){
			$subShowForm = $('#subtitle_show');
			$subShowMovieId = $('input[name="movie.id"]', $subShowForm);
			$subShowPath = $('input[name="subtitle.path"]', $subShowForm);
		}

		$subShowMovieId.val(info.movieId);
		$subShowPath.val(info.subpath);
		$subShowForm.submit();
		return false;
	}

	function trashSubtitleCallback(){
		var info = getSubtitleRow($(this)), 
			path = info.subpath,
			movieId = info.movieId;
		$updatingTr = info.$mainRow;
		DialogConfirm.show('Are you sure to remove from database / file system the subtitle '+path+'?',
			{
				url:urlTrashSubtitle,
				success: function(response){
					updateMovieInfo($updatingTr, response);
					DialogConfirm.hide();
				},
				message:'Subtitle file trashing',
				data:{
					movieId:movieId,
					locationId: locationId,
					locationPath: locationPath,
					subpath:path
				}
			});
		return false;
	}

	function removeSubtitleCallback(){

		var info = getSubtitleRow($(this)), 
			path = info.subpath,
			movieId = info.movieId;

		$updatingTr=info.$subSelector; 
		DialogConfirm.show('Are you sure to remove from database the subtitle '+path+'?',
			{
				url:urlRemoveSubtitle,
				success: function(response){
					$updatingTr.html('');
					DialogConfirm.hide();
				},
				message:'Subtitle database deletion',
				data:{
					movieId:movieId,
					locationId: locationId,
					path:path
				}
			});
		return false;
	}


	function editSubtitleCallback(){
		if (!$stDialog){
			$stDialog = $('#locations_subtitle_dialog').on('shown.bs.modal', function(){$stLanguage.focus();});
			$stPathText = $('.path', $stDialog);
			$stLanguage = $('select', $stDialog).val('English');
			$stNormalize = $('.checkbox', $stDialog);
			$stMovie = $('input[name="movie.id"]', $stDialog);
			$stPathInput = $('input[name="file.path"]', $stDialog);
			setupAjaxModal($stDialog, {
				message : 'Subtitle update',
				success : function(response){
					$stDialog.modal('hide');
					$updatingTr.replaceWith(response);
					setupEventHandlers();								
				}
			});
		}

		var info = getSubtitleRow($(this)), 
			movieId=info.movieId,
		    language=info.$subpath.attr('data-language'), 
		    path=info.subpath;

		$updatingTr=info.$subSelector;
		$stPathText.text(path);
		$stPathInput.val(path);
		$stMovie.val(movieId);
		if (language) $stLanguage.val(language);
		$stDialog.modal('show');
		return false;
	}

	function fetchSubtitlesCallback(event, title){
		if (!$fetchDialog){
			$fetchDialog = $('#locations_subtitle_fetch_dialog').on('shown.bs.modal', function(){
				$fetchSelection.focus();
				fetchDialogSettings.submit.click();
			});
			$fetchTitleText = $('.title', $fetchDialog);
			$fetchLanguage = $('select[name="language"]', $fetchDialog).val('English');
			$fetchSelection = $('select[name="subtitle"]', $fetchDialog);
			$fetchMovie = $('input[name="movie.id"]', $fetchDialog);
			$fetchDirCreate = $('input[name="dir_creation"]', $fetchDialog);
			$fetchTitle = $('input[name="title"]', $fetchDialog);
			fetchDialogSettings = setupAjaxModal($fetchDialog, {
				message : 'Subtitles fetch',
				success : function(response){
					if (fetchingMatches){
						if (!response){
							$fetchDialog.modal('hide');
							var title=prompt("The current title is not matched, please enter it differently",title);
							if (title){
								fetchSubtitlesCallback(null, title);
							}
							return;
						}
						fetchingMatches=false;
						fetchDialogSettings.settings.message='Fetching subtitle';
						$fetchSelection.html(response);
					} else {
						updateMovieInfo($updatingTr, response);
						if ($fetchDirCreate.prop('checked')){
							$fetchDialog.modal('hide');
						}
					}
					fetchDialogSettings.hideProgress();
				}
			});
		}

		fetchingMatches=true;
		fetchDialogSettings.settings.message='Retrieving correct title';
		$updatingTr=getMainRow($(this));
		if (event){
			$fetchTitleText.text($('.title', $updatingTr).text());
			$fetchSelection.html('');
			$fetchDirCreate.prop('checked', false);
			$fetchMovie.val($updatingTr.attr('data-movie-id'));
		}
		$fetchTitle.val(title || null)
		$fetchDialog.modal('show');
		return false;
	}

	function refreshSubtitlesCallback(){
		var $main=getMainRow($(this));
		ajaxPost({
			url: urlRefreshInfo,
			data: {
				locationId: locationId,
				movieId: $main.attr('data-movie-id'),
				path: locationPath, 
			},
			message: 'Refreshing subtitles',
			success: function(response){
				updateMovieInfo($main, response);
			}
		});
		return false;
	}

	function cleanSubtitlesCallback(){
		var $main=getMainRow($(this)), title = $('.title', $main)
		DialogConfirm.show('Are you sure to remove the unused subtitles from the movie '+title.text()+'?',
			{
				url: urlCleanSubtitles,
				data: {
					locationId: locationId,
					movieId: $main.attr('data-movie-id'),
					path: locationPath, 
				},
				message: 'Cleaning subtitles',
				success: function(response){
					updateMovieInfo($main, response);
					DialogConfirm.hide();
				}
			});
		return false;
	}

	function getMainRow($subSelector){
		while ($subSelector.length){
			if ($subSelector.attr('data-movie-id')) return $subSelector;
			$subSelector=$subSelector.parent();
		}		
	}

	function getSubtitleRow($subSelector){
		while ($subSelector.length){
			if ($subSelector.hasClass('subtitle')) {
				var movieId, $tmp=$subSelector;
				while (!movieId && ($tmp=$tmp.prev()).length){
					movieId=$tmp.attr('data-movie-id');
				}
				$path=$subSelector.find('.path');
				return {
					$subSelector: $subSelector, 
					$mainRow:  $tmp,
					$subpath: $path,
					subpath: $.trim($path.text()),
					movieId: movieId
				};
			}
			$subSelector=$subSelector.parent();
		}		
	}

	function getMovieId($languageSelector){
		var $tr=getMainRow($languageSelector); 
		return [$tr.attr('data-movie-id'), $tr.find('.title').text()];
	}


	locationId = $locationsSyncSelector.attr('data-location-id');
	locationPath = $locationsSyncSelector.attr('data-location-path'); 
	urlRemoveSubtitle = $locationsSyncSelector.attr('data-remove-subtitle-url');
	urlTrashSubtitle = $locationsSyncSelector.attr('data-trash-subtitle-url');
	urlEditMovie = $locationsSyncSelector.attr('data-edit-movie-url');
	urlRemoveMovie = $locationsSyncSelector.attr('data-remove-movie-url');
	urlRefreshInfo = $locationsSyncSelector.attr('data-info-movie-url');
	urlCleanSubtitles = $locationsSyncSelector.attr('data-clean-subtitles-url');

	$ref_add = $('#ref-add', $locationsSyncSelector);
	$ref_remove = $('#ref-remove', $locationsSyncSelector);

	if ($('td', $problemDialog).length){
		$problemDialog.modal('show');
	}
	setupEventHandlers();
	movieEdition(getMovieId);
	checkPlusMinusMovies();
}