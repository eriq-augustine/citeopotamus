#!/usr/bin/perl
use strict;
use warnings;

use Carp;
use Cwd;
use File::Copy;

use constant ROOT_DIR => getcwd().'/data/';

sub dir_status {
   if ($ENV{DEBUG}) {
      print("current directory: ".getcwd()."\n");
   }
}

sub read_dir {
   my ($dir_handle) = @_;

   return grep { $_ !~ m/[.]+/ } readdir($dir_handle);
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
   my ($REF_ROOT) = @_;

   opendir(my $REF_DIR, getcwd()) or croak('Unable to open current directory');

   my $DIR_BEGIN = telldir($REF_DIR);

   # A loop to pull all sub directories up to current directory
   for my $sub_dir (read_dir($REF_DIR)) {
      dir_map($sub_dir, sub {
         hoist_references($REF_ROOT);
      });
   }
   closedir($REF_DIR);

   opendir($REF_DIR, getcwd()) or croak('Unable to open current directory');

   for my $sub_dir (read_dir($REF_DIR)) {
      if (-d $sub_dir) {
         my ($abs_sub_dir, $parent_dir) = (getcwd()."/$sub_dir", getcwd().'/..');
         print("move '$abs_sub_dir' '$parent_dir\n'");

         if (!$ENV{DEBUG}) {
            #move($abs_sub_dir, $parent_dir) or croak("error moving file: $!");
            `mv "$abs_sub_dir" "$parent_dir"`;
            #print `pwd`;
            #print `ls`;
         }
      }
   }

   closedir($REF_DIR);

}

sub fix_ref_dir {
   my ($paper_dir) = @_;

   my $success = dir_map("$paper_dir/references", sub {
      my $reference_root = getcwd();
      opendir(my $REF_DIR, $reference_root) or croak('Unable to open cwd');

      for my $sub_dir (read_dir($REF_DIR)) {
         dir_map($sub_dir, sub {
            hoist_references($reference_root);
         });
      }
      closedir($REF_DIR);

      chdir(q{..});
   });

   if (!$success) {
      print({*STDERR} "Failed to map function on dir $paper_dir/references\n");
   }
}

sub main {
   if (chdir(ROOT_DIR)) {
      opendir(my $DIR_HANDLE, getcwd()) or croak('Unable to open directory '.
                                                 ROOT_DIR);

      for my $paper_dir (read_dir($DIR_HANDLE)) {
         chomp($paper_dir);

         if ($paper_dir !~ m/dynamo/ && -d $paper_dir) {
            if ($ENV{DEBUG}) { print("fixing $paper_dir\n"); }

            fix_ref_dir($paper_dir);
         }

      }

      closedir($DIR_HANDLE);
   }
   else { print({*STDERR} "Unable to chdir to ".ROOT_DIR."\n"); }
}

main();
