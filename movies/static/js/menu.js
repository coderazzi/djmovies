var mainDiv;
var menuGroups={};
var menuItems={};

function menu_add(name, group, callback){
	if (!mainDiv) mainDiv = $('#menu-main');
	var ret=$('<div class="menu-item">'+name+'</div>').appendTo(mainDiv);
	menuItems[group].push(ret);
	ret.click(function(event){
		if (ret.hasClass('menu-item-enabled')){
			callback(event);
		}
	});
	return ret;
}

function register_menu_group(name, callback){
	menuGroups[name]=callback;
	menuItems[name]=[];
}

function update_groups(){
	for(var group in menuGroups) 
		if (menuGroups.hasOwnProperty(group)) {
			var enabled = menuGroups[group]();
			var items=menuItems[group];
			for (var sel in items){
				if (enabled){
					items[sel].addClass('menu-item-enabled');
				} else {
					items[sel].removeClass('menu-item-enabled');					
				}
			}
  		}	
}