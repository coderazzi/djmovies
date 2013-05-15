function setupLocationsSync($locationsSyncSelector){

	var $problemDialog = $('#locations_sync_problems_dialog');

	var $stDialog, $stTitleText, $stPathText, $stPathInput;
	var $stLanguage, $stMovie, $stNormalize;	

	var $fetchDialog, $fetchTitleText;
	var $fetchLanguage, $fetchMovie, $fetchSelection;	

	var $subShowForm, $subShowMovieId, $subShowPath;
	
	var $updatingTr;

	var locationId, locationPath, fetchingMatches, fetchDialogSettings;
	var urlRemoveSubtitle, urlEditMovie, urlRemoveMovie, urlRefreshInfo, urlTrashSubtitle;

	function setupEventHandlers(){
		$('.edit-movie').click(editMovieCallback);
		$('.remove-movie').click(removeMovieCallback);
		$('.edit-subtitle').off('click').click(editSubtitleCallback);
		$('.remove-subtitle').off('click').click(removeSubtitleCallback);
		$('.fetch-subtitle').off('click').click(fetchSubtitlesCallback);
		$('.refresh-subtitles').off('click').click(refreshSubtitlesCallback);
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
		} else {
			$tr.remove();
		}
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
			$stDialog = $('#locations_subtitle_dialog').on('shown', function(){$stLanguage.focus();});
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
		    language=$path.attr('data-language'), 
		    path=info.subpath;

		$updatingTr=info.$subSelector;
		$stPathText.text(path);
		$stPathInput.val(path);
		$stMovie.val(movieId);
		if (language) $stLanguage.val(language);
		$stDialog.modal('show');
		return false;
	}

	function fetchSubtitlesCallback(){
		if (!$fetchDialog){
			$fetchDialog = $('#locations_subtitle_fetch_dialog').on('shown', function(){
				$fetchSelection.focus();
				fetchDialogSettings.submit.click();
			});
			$fetchTitleText = $('.title', $fetchDialog);
			$fetchLanguage = $('select[name="language"]', $fetchDialog).val('English');
			$fetchSelection = $('select[name="subtitle"]', $fetchDialog);
			$fetchMovie = $('input[name="movie.id"]', $fetchDialog);
			fetchDialogSettings = setupAjaxModal($fetchDialog, {
				message : 'Subtitles fetch',
				success : function(response){
					if (fetchingMatches){
						fetchingMatches=false;
						fetchDialogSettings.settings.message='Fetching subtitle'
						$fetchSelection.html(response);
					} else {
						updateMovieInfo($updatingTr, response);
					}
					fetchDialogSettings.hideProgress();
				}
			});
		}

		fetchingMatches=true;
		fetchDialogSettings.settings.message='Retrieving correct title';
		$updatingTr=getMainRow($(this));
		$fetchTitleText.text($('.title', $updatingTr).text());
		$fetchSelection.html('');
		$fetchMovie.val($updatingTr.attr('data-movie-id'));
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
				return {
					$subSelector: $subSelector, 
					$mainRow:  $tmp,
					subpath: $.trim($subSelector.find('.path').text()),
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

	if ($('td', $problemDialog).length){
		$problemDialog.modal('show');
	}
	setupEventHandlers();
	movieEdition(getMovieId);
}