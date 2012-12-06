#!/usr/bin/perl
use strict;
use warnings;

use Carp;
use Cwd;
use File::Copy;

use constant ROOT_DIR => getcwd().'/fix_data/';

sub dir_status {
   if ($ENV{DEBUG}) {
      print("current directory: ".getcwd()."\n");
   }
}

sub read_dir {
   my ($dir_handle) = @_;

   return grep { $_ !~ m/^[.]/ } readdir($dir_handle);
}

sub dir_map {
   my ($success, $dir_name, $anon_func) = (0, @_);

   if (-d $dir_name && chdir($dir_name)) {
      dir_status();
      &$anon_func();
      $success = 1;
      chdir(q{..});
      dir_status();
   }

   return $success;
}

sub hoist_references {
   my ($num_files, $ref_root) = (0, @_);

   opendir(my $CURR_DIR, getcwd()) or croak('Unable to open current directory');

   for my $sub_dir (read_dir($CURR_DIR)) {
      $num_files++;
      if (-d $sub_dir) {
         if (chdir($sub_dir)) {
            my $has_files = hoist_references($ref_root);
            chdir(q{..});

            if (!$has_files) {
               dir_status();
               if ($ENV{DEBUG}) { print "rm -rf $sub_dir\n"; }
               else { `rm -rf $sub_dir`; }
               next;
            }
         }

         if (!-d "$ref_root/$sub_dir") {
            dir_status();
            if ($ENV{DEBUG}) { print "mv '$sub_dir' '$ref_root'\n"; }
            else { `mv "$sub_dir" "$ref_root"`; }
         }
      }
   }

   closedir($CURR_DIR);

   return $num_files;
}

sub fix_ref_dir {
   my ($paper_dir) = @_;

   if (chdir("$paper_dir/references")) {
      my $ref_root = getcwd();

      hoist_references($ref_root);

      chdir(q{../..});
   }
   else {
      print("rm -rf \"$paper_dir\"\n");
   }
}

sub main {
   if (chdir(ROOT_DIR)) {
      opendir(my $DIR_HANDLE, getcwd()) or croak('Unable to open directory '.
                                                 ROOT_DIR);

      for my $paper_dir (read_dir($DIR_HANDLE)) {
         chomp($paper_dir);

         if (-d $paper_dir) {
            if ($ENV{DEBUG}) { print("$paper_dir\n"); }

            fix_ref_dir($paper_dir);
         }

      }

      closedir($DIR_HANDLE);
   }
   else { print({*STDERR} "Unable to chdir to ".ROOT_DIR."\n"); }
}

main();
