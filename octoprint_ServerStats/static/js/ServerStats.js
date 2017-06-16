/*
 * View model for OctoPrint-ServerStats
 *
 * Author: Jeff Wight
 * License: AGPLv3
 */
$(function() {
    function ServerstatsViewModel(parameters) {
        var self = this;

        // assign the injected parameters, e.g.:
        // self.loginStateViewModel = parameters[0];
        // self.settingsViewModel = parameters[1];

        // TODO: Implement your plugin's view model here.
    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        ServerstatsViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        [ /* "loginStateViewModel", "settingsViewModel" */ ],

        // e.g. #settings_plugin_ServerStats, #tab_plugin_ServerStats, ...
        [ /* ... */ ]
    ]);
});
