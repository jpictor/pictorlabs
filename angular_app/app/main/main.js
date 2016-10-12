'use strict';

angular.module('myApp.main', ['ngRoute'])

    .config(['$routeProvider', function ($routeProvider) {
        $routeProvider.when('/fs', {
            templateUrl: 'main/main.html',
            controller: 'MainCtrl'
        });
        $routeProvider.when('/fs/:parentId', {
            templateUrl: 'main/main.html',
            controller: 'MainCtrl'
        });


    }])

    .controller('MainCtrl', function ($scope, $window, $location, $routeParams, $sce, Restangular) {
        $scope.parentId = $routeParams.parentId;
        $scope.entity = null;
        $scope.typeFilter = 'all';
        $scope.setTypeFilter = function (_type) {
            if ($scope.busy) return;
            $scope.typeFilter = _type;
            $scope.loadItems(true);
        }
        $scope.isFilterActive = function (_type) {
            return _type == $scope.typeFilter;
        }
        $scope.orderFilter = '-timestamp';
        $scope.setOrderFilter = function (_order) {
            if ($scope.busy) return;
            $scope.orderFilter = _order;
            $scope.loadItems(true);
        }
        $scope.isOrderActive = function (_order) {
            return _order == $scope.orderFilter;
        }
        $scope.userGuid = null;
        $scope.setUserGuid = function() {
            if ($scope.busy) return;
            $scope.loadItems(true);
        }
        $scope.oembedHtml = '';
        $scope.setParentEntity = function(parent) {
            if (parent.num_children > 0) {
                $location.path('/fs/' + parent.id);
            }
        }

        $scope.busy = false;
        $scope.pageNum = 1;
        $scope.totalItemCount = 0;
        $scope.items = [];
        $scope.loadItems = function (clearItems) {
            if ($scope.busy) return;
            $scope.busy = true;
            if (clearItems) {
                $scope.totalItemCount = 0;
                $scope.items.length = 0;
                $scope.pageNum = 1;
                $window.scrollTo(0, 0);
            } else {
                $scope.pageNum += 1;
            }
            var params = {
                page: $scope.pageNum,
                page_size: 30,
                ordering: $scope.orderFilter
            };
            if ($scope.typeFilter != 'all') {
                params.type = $scope.typeFilter;
            }
            if ($scope.userGuid) {
                params.user_guid = $scope.userGuid;
            }
            if ($scope.parentId) {
                params.parent = $scope.parentId;
            }
            Restangular.one('pictorlabs/entity/', $scope.parentId).get().then(function(entity) {
                $scope.entity = entity;
                if ($scope.entity.doc && $scope.entity.doc.html) {
                    $scope.oembedHtml = $sce.trustAsHtml($scope.entity.doc.html);
                }
            });
            Restangular.all('pictorlabs/entity/').getList(params).then(function(items) {
                _.each(items, function(x) { $scope.items.push(x) }); 
                $scope.totalItemCount = items._count;
                $scope.busy = false;
            }, function () {
                $scope.busy = false;
            });
       }
       $scope.loadItems(true);
    });
