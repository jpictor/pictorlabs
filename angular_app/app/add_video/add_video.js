'use strict';

angular.module('myApp.add_video', ['ngRoute'])

    .config(['$routeProvider', function ($routeProvider) {
        $routeProvider.when('/add-video', {
            templateUrl: 'add_video/add_video.html',
            controller: 'AddVideoCtrl'
        });
    }])

    .controller('AddVideoCtrl', function ($scope, $rootScope, $location, Restangular) {
        $scope.url = null;
        $scope.busy = false;
        $scope.submit = function () {
            if ($scope.busy) {
                return;
            }
            $scope.busy = true;
            var postData = {url: $scope.url};
            Restangular.all('pictorlabs/add_video').post(postData).then(function(chkResp) {
                $scope.busy = false;
                $location.path('/app/');
            }, function(response) {
                $scope.busy = false;
                $scope.message = 'Failed to add URL';
            });
        }
    });
