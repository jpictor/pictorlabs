'use strict';

angular.module('myApp.auth.login', ['ngRoute'])

    .config(['$routeProvider', function ($routeProvider) {
        $routeProvider.when('/login', {
            templateUrl: 'auth/login.html',
            controller: 'LoginCtrl'
        });
    }])

    .controller('LoginCtrl', function ($scope, $rootScope, $location, Restangular) {
        $scope.inputUsername = null;
        $scope.inputPassword = null;
        $scope.incorrectPassword = false;

        $scope.submit = function () {
            var postData = {username: $scope.inputUsername, password: $scope.inputPassword};
            Restangular.all('session/login').post(postData).then(function(chkResp) {
                $rootScope.userIsAuthenticated = true;
                $location.path('/app/');
            }, function(response) {
                $scope.incorrectPassword = true;
            });
        }
    });
